import { Item} from "../models.js";
import amazonAsin from 'amazon-asin'
const enrichOrderInfo = async (item) => {
  if (item.orderInfo && item.orderInfo.url) {
    let { ASIN, url, urlTld } = await amazonAsin.asyncParseAsin(item.orderInfo.url)
    if (ASIN) {
      item.orderInfo.retailer = "AMZ"
      item.orderInfo.retailerId = ASIN;
    } else {
      if (item.orderInfo.url.indexOf("heb.com") > 0) {
        item.orderInfo.retailer = "HEB"
      } else if (item.orderInfo.url.indexOf("chewy.com") > 0) {
        item.orderInfo.retailer = "CHY"
      } else if (item.orderInfo.url.indexOf("cynch.com") > 0) {
        item.orderInfo.retailer = "CYH"
      }
    }
  }
  return item
}


export const findItemController = async (req, res) => {
  try {
    const item = await Item.findById(req.params.itemId);

    if (!item) {
      return res.status(404).json({
        status: "fail",
        message: "Item with that ID not found",
      });
    }

    res.status(200).json(item);
  } catch (error) {
    res.status(500).json({
      status: "error",
      message: error.message,
    });
  }
};

export const findAllItemsController = async (req, res) => {
  try {
    const items = await Item.find()
    res.status(200).json(items);
  } catch (error) {
    res.status(500).json({
      status: "error",
      message: error.message,
    });
  }
};


export const createItemController = async (req, res) => {
  try {

    const item = await Item.create(req.body);
    res.status(200).json(item);
  } catch (error) {
    res.status(500).json({
      status: "error",
      message: error.message,
    });
  }
};

export const updateItemController = async (req, res) => {
  try {

    const item = await Item.findByIdAndUpdate(req.params.itemId, req.body);
    res.status(200).json(item);
  } catch (error) {
    console.error(error)
    res.status(500).json({
      status: "error",
      message: error.message,
    });
  }
};

export const deleteItemController = async (req, res) => {
  try {
    const item = await Item.findByIdAndDelete(req.params.itemId);
    res.status(200).json(item);
  } catch (error) {
    res.status(500).json({
      status: "error",
      message: error.message,
    });
  }

};