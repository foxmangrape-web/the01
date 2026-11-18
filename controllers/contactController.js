const asyncHandler = require("express-async-handler");
const Contact = require("../models/contactModel");

// @desc Get all contacts
// @route GET /contacts
const getAllContacts = asyncHandler(async (req, res) => {
  const contacts = await Contact.find();
  res.render("index", { contacts: contacts });
});

// @desc View add contact form
// @route GET /contacts/add
const addContactForm = asyncHandler((req, res) => {
  res.render("add");
});

// @desc Create a contact
// @route POST/contacts/add
const createContact = asyncHandler(async (req, res) => {
  // console.log(req.body);
  const { name, email, phone } = req.body;
  const contact = Contact.create({
    name,
    email,
    phone,
  });
  res.redirect("/contacts");
});

// @desc Get contact
// @route GET /contacts/:id
const getContact = asyncHandler(async (req, res) => {
  const contact = await Contact.findById(req.params.id);
  res.render("update", { contact: contact });
});

// @desc Update contact
// @route PUT /contacts/:id
const updateContact = asyncHandler(async (req, res) => {
  const id = req.params.id;
  const { name, email, phone } = req.body;
  const updatedContact = await Contact.findByIdAndUpdate(
    id,
    { name, email, phone },
    { new: true }
  );
  res.redirect("/contacts");
});

// @desc Delete contact
// @route DELETE /contacts/:id
const deleteContact = asyncHandler(async (req, res) => {
  const { id } = req.params;

  // ID 유효성 검사
  if (!id) {
    return res.status(400).json({ message: "유효하지 않은 ID입니다." });
  }

  // 문서 삭제 시도
  const result = await Contact.findByIdAndDelete(id);

  // 문서가 존재하지 않을 때의 처리
  if (!result) {
    return res.status(404).json({ message: "해당 연락처를 찾을 수 없습니다." });
  }

  res.redirect("back");
});

module.exports = {
  getAllContacts,
  createContact,
  getContact,
  updateContact,
  deleteContact,
  addContactForm,
};
