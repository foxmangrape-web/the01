const getDatabase = require("../config/dbConnect");
const database = getDatabase();

const User = {
  create({ username, password }) {
    if (!username || !password) {
      throw new Error("아이디와 비밀번호를 입력해 주세요.");
    }

    const result = database
      .prepare("INSERT INTO users (username, password) VALUES (?, ?)")
      .run(username, password);
    return this.findById(result.lastInsertRowid);
  },

  findOne({ username }) {
    return database
      .prepare("SELECT id AS _id, username, password FROM users WHERE username = ?")
      .get(username) || null;
  },

  findById(id) {
    return database
      .prepare("SELECT id AS _id, username, password FROM users WHERE id = ?")
      .get(Number(id)) || null;
  },
};

module.exports = User;
