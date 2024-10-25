import { ServiceSubject, checkRecurringTasks } from "../models.js";
//import { getBucket } from "../../../common/db.js";
import _ from "lodash"
export const findServiceSubjectController = async (req, res) => {
  try {
    const subject = await ServiceSubject.findOne({ _id: req.params.serviceSubjectId, owner: req.user._id });

    if (!subject) {
      return res.status(404).json({
        status: "fail",
        message: "ServiceSubject with that ID not found",
      });
    }

    res.status(200).json(subject);
  } catch (error) {
    res.status(500).json({
      status: "error",
      message: error.message,
    });
  }
};

export const findAllServiceSubjectsController = async (req, res) => {
  try {
    const subjects = await ServiceSubject.find({ owner: req.user._id })
    res.status(200).json(subjects);
  } catch (error) {
    res.status(500).json({
      status: "error",
      message: error.message,
    });
  }
};


export const createServiceSubjectController = async (req, res) => {
  try {
    req.body.owner = req.user._id;
    const subject = await ServiceSubject.create(req.body);
    await checkRecurringTasks(subject)
    res.status(200).json(subject);
  } catch (error) {
    res.status(500).json({
      status: "error",
      message: error.message,
    });
  }
};










export const updateServiceSubjectController = async (req, res) => {
  req.body.owner = req.user._id;
  try {
    let taskNames = req.body.tasks.filter((t) => !t.completed).map((t) => t.name)
    if ((new Set(taskNames)).size !== taskNames.length) {
      return res.status(400).json({
        status: "error",
        message: "Bad Request: multiple tasks with the same name"
      })
    }
    taskNames = req.body.recurringTasks.map((t) => t.name)
    if ((new Set(taskNames)).size !== taskNames.length) {
      return res.status(400).json({
        status: "error",
        message: "Bad Request: multiple recurring tasks with the same name"
      })
    }
    const subject = await ServiceSubject.findById(req.params.serviceSubjectId);

    const updateSubject = await ServiceSubject.findByIdAndUpdate(req.params.serviceSubjectId, req.body, { new: true })
    await checkRecurringTasks(subject)
    res.status(200).json(subject);
  } catch (error) {
    console.error(error)
    res.status(500).json({
      status: "error",
      message: error.message,
    });
  }
};

export const deleteServiceSubjectController = async (req, res) => {
  try {
    const subject = await ServiceSubject.find({ _id: req.params.serviceSubjectId, owner: req.user._id });
    if (subject) {
      await ServiceSubject.deleteOne({ _id: subject._id })
      res.status(200).json(subject);
    } else {
      res.status(404).json({
        status: "error",
        message: "Subject not found",
      });
    }
  } catch (error) {
    res.status(500).json({
      status: "error",
      message: error.message,
    });

  }
};


export const uploadDocumentController = async (req, res) => {
  console.log(req.body, req.file)
  try {
    const subject = await ServiceSubject.findById(req.params.serviceSubjectId);
    subject.documents.push({
      gridId: req.file.id,
      name: req.body.name
    });
    let updated = await subject.save()
    res.status(200).json(updated);
  } catch (error) {
    res.status(500).json({
      status: "error",
      message: error.message,
    });
  }
};
// export const downloadDocumentController = async (req, res) => {
//   let gfs = getBucket()
//   let subject = await ServiceSubject.findById(req.params.serviceSubjectId)
//   let index = subject.documents.findIndex((doc) => doc._id == req.params.documentId)
//   console.log(req.params.documentId, subject.documents)
//   if (index >= 0) {
//     let gridId = subject.documents[index]
//     gfs
//       // create a read stream from gfs...
//       .createReadStream({ _id: gridId })
//       // and pipe it to Express' response
//       .pipe(res);
//   } else {
//     res.status(404);
//   }
// };
