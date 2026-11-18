const asyncHandler = require("express-async-handler");
const User = require("../models/userModel");
const bcrypt = require("bcrypt");
const jwt = require("jsonwebtoken");
const path = require("node:path");
require("dotenv").config({ path: path.join(__dirname, "..", ".env") });
const jwtSecret = process.env.JWT_SECRET;
if (!jwtSecret) {
  throw new Error("JWT_SECRET을 프로젝트 루트의 .env 또는 환경변수로 설정해 주세요.");
}

/**
 * 사용자 등록
 */

//@desc Register Page
//@route GET /register
const getRegister = (req, res) => {
  res.render("register");
};

// @desc Register user
// @route POST /register
const registerUser = asyncHandler(async (req, res) => {
  const { username, password, password2 } = req.body;
  if (!username || !password || password !== password2) {
    return res.status(400).send("아이디와 비밀번호를 확인해 주세요.");
  }

  if (User.findOne({ username })) {
    return res.status(409).send("이미 사용 중인 아이디입니다.");
  }

  const hashedPassword = await bcrypt.hash(password, 10);
  const user = User.create({ username, password: hashedPassword });
  return res.status(201).json({
    message: "Register successful",
    user: { _id: user._id, username: user.username },
  });
});

/**
 * 사용자 로그인 / 로그아웃
 */

//@desc Get login page
//@route GET /
const getLogin = (req, res) => {
  res.render("home");
};

//@desc Login user
//@route POST /
const loginUser = asyncHandler(async (req, res) => {
  const { username, password } = req.body;
  const user = User.findOne({ username });
  if (!user) {
    return res.status(401).json({ message: "일치하는 사용자가 없습니다." });
  }
  const isMatch = await bcrypt.compare(password, user.password);

  if (!isMatch) {
    return res.status(401).json({ message: "비밀번호가 일치하지 않습니다." });
  }

  const token = jwt.sign(
    { id: user._id, username: user.username },
    jwtSecret,
    { expiresIn: "1h" }
  );
  res.cookie("token", token, { httpOnly: true, sameSite: "lax" });

  return res.redirect("/contacts");
});

// @desc Logout
// @route GET /logout
const logout = (req, res) => {
  res.clearCookie("token", { httpOnly: true, sameSite: "lax" });
  return res.redirect("/");
};

module.exports = { getRegister, registerUser, getLogin, loginUser, logout };