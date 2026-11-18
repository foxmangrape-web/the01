// const express = require("express");
// const router = express.Router();
// const Contact = require("../models/contactModel");
// const {
//   getAllContacts,
//   createContact,
//   getContact,
//   updateContact,
//   deleteContact,
// } = require("../controllers/contactController");

// router.route("/").get(getAllContacts).post(createContact);

// router.route("/:id").get(getContact).put(updateContact).delete(deleteContact);

// module.exports = router;


const express = require("express");
const router = express.Router();
const cookieParser = require("cookie-parser");
const checkLogin = require("../middlewares/checkLogin");
const {
  getAllContacts,
  createContact,
  getContact,
  updateContact,
  deleteContact,
  addContactForm,
} = require("../controllers/contactController");


router.route("/").get(checkLogin, getAllContacts);

router
  .route("/add")
  .get(checkLogin, addContactForm)
  .post(checkLogin, createContact);

router
  .route("/:id")
  .get(checkLogin, getContact)
  .put(checkLogin, updateContact)
  .delete(checkLogin, deleteContact);

module.exports = router;
