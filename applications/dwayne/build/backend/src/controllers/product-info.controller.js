import amazonAsin from "amazon-asin"
import axios from 'axios'
const formatPrice = (price) => {
    if (Number.isInteger(price)) {
        return price / 100
    } else {
        return price;
    }
}
export const getProductInfo = async (req, res) => {
    let url = req.body.url;
    let result = await amazonAsin.asyncParseAsin(url);
    let ASIN = result.ASIN;
    if (ASIN) {
        console.log(`Getting info for ${ASIN}`)
        let resp = await axios({
            url: 'https://api.sellerapp.com/amazon/us/research/new/free_tool/product_details', 
            headers: {
                "X-Client":"dashboard"
            },
            params: {
                "product_specifications": 1,
                "potential_detail": 1,
                "price_detail": 1,
                "fee_detail": 1,
                "geo": "us",
                "productIds": ASIN,
            }, 
            method: "GET"
        })
        res.status(200).json({
            retailerId: ASIN,
            retailer: "AMZ",
            price: formatPrice(resp.data.data[0].price_details.listing_price_new)
        })
    } else {
        res.status(200).json({})
    }

    
}