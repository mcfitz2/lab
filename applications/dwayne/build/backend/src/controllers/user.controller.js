import { User} from "../models.js";

export const findUserController = async (req, res) => {
  if (req.params.userId == "self") {
    req.params.userId = req.user._id
  }
  try {
    const user = await User.findById(req.params.userId);

    if (!user) {
      return res.status(404).json({
        status: "fail",
        message: "User with that ID not found",
      });
    }

    res.status(200).json(user);
  } catch (error) {
    res.status(500).json({
      status: "error",
      message: error.message,
    });
  }
};

// export const findAllUsersController = async (req, res) => {
//   try {
//     const users = await User.find()
//     res.status(200).json(users);
//   } catch (error) {
//     res.status(500).json({
//       status: "error",
//       message: error.message,
//     });
//   }
// };


// export const createUserController = async (req, res) => {
//   try {
//     const user = await User.create(req.body);
//     res.status(200).json(user);
//   } catch (error) {
//     res.status(500).json({
//       status: "error",
//       message: error.message,
//     });
//   }
// };

export const updateUserController = async (req, res) => {
  try {
    const user = await User.findByIdAndUpdate(req.params.userId, {$set:{
      locations: req.body.locations,
      units: req.body.units
    }});
    console.log(req.body, user)

    res.status(200).json(user);
  } catch (error) {
    console.error(error)
    res.status(500).json({
      status: "error",
      message: error.message,
    });
  }
};

// export const deleteUserController = async (req, res) => {
//   try {
//     const user = await User.findByIdAndDelete(req.params.userId);
//     res.status(200).json(user);
//   } catch (error) {
//     res.status(500).json({
//       status: "error",
//       message: error.message,
//     });
//   }

//};