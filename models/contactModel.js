const getDatabase = require("../config/dbConnect");
const database = getDatabase();

const contactColumns = "id AS _id, name, email, phone, office, createdAt, updatedAt";

const toId = (id) => {
  const parsedId = Number(id);
  return Number.isSafeInteger(parsedId) && parsedId > 0 ? parsedId : null;
};

const validateContact = ({ name, phone }) => {
  if (!name || !phone) {
    throw new Error("이름과 전화번호는 꼭 입력해 주세요.");
  }
};

const Contact = {
  find() {
    return database.prepare(`SELECT ${contactColumns} FROM contacts ORDER BY id`).all();
  },

  findById(id) {
    const parsedId = toId(id);
    if (!parsedId) return null;

    return database
      .prepare(`SELECT ${contactColumns} FROM contacts WHERE id = ?`)
      .get(parsedId) || null;
  },

  create({ name, email = null, phone, office = null }) {
    validateContact({ name, phone });
    const result = database
      .prepare("INSERT INTO contacts (name, email, phone, office) VALUES (?, ?, ?, ?)")
      .run(name, email, phone, office);
    return this.findById(result.lastInsertRowid);
  },

  findByIdAndUpdate(id, { name, email = null, phone, office = null }) {
    const parsedId = toId(id);
    if (!parsedId) return null;
    validateContact({ name, phone });

    const result = database
      .prepare(
        "UPDATE contacts SET name = ?, email = ?, phone = ?, office = ?, updatedAt = datetime('now') WHERE id = ?"
      )
      .run(name, email, phone, office, parsedId);

    return result.changes ? this.findById(parsedId) : null;
  },

  findByIdAndDelete(id) {
    const contact = this.findById(id);
    if (!contact) return null;
    database.prepare("DELETE FROM contacts WHERE id = ?").run(contact._id);
    return contact;
  },

  deleteOne(filter = {}) {
    const parsedId = toId(filter._id || filter.id);
    if (!parsedId) return { deletedCount: 0 };
    const result = database.prepare("DELETE FROM contacts WHERE id = ?").run(parsedId);
    return { deletedCount: result.changes };
  },
};

module.exports = Contact;
