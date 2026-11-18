const jwt = require("jsonwebtoken");
const path = require("node:path");
require("dotenv").config({ path: path.join(__dirname, "..", ".env") });
const jwtSecret = process.env.JWT_SECRET;
if (!jwtSecret) {
  throw new Error("JWT_SECRET을 sqlite/.env 또는 환경변수로 설정해 주세요.");
}

const checkLogin = async (req, res, next) => {
  res.setHeader("Cache-Control", "no-cache, no-store, must-revalidate");
  const token = req.cookies.token;

  if (!token) {
    return res.redirect("/");
  }

  try {
    const decoded = jwt.verify(token, jwtSecret);
    req.username = decoded.username;
    next();
  } catch (error) {
    return res.status(401).json({ message: "로그인이 필요합니다." });
  }
};

module.exports = checkLogin;
