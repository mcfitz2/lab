import {Strategy, ExtractJwt} from 'passport-jwt'
import passport from 'passport'
import {User} from "../models.js"
import jwt from 'node-jsonwebtoken'

const SECRET_KEY = "catsarecool"

var cookieExtractor = function(req) {
    var token = null;
    if (req && req.cookies && req.cookies['SESSIONID']) {
        token = req.cookies['SESSIONID'];
    } else if (req && req.headers['auth-token']) {
        token = req.headers['auth-token']
    }
    return token;
};

passport.use(new Strategy({jwtFromRequest: cookieExtractor, secretOrKey:SECRET_KEY}, async function(jwt_payload, done) {
    try {
        let user = await User.findById(jwt_payload.sub)
        if (user) {
            return done(null, user);
        } else {
            return done(null, false);
            // or you could create a new account
        }
    } catch (err) {
        console.error(err)
        return done(err, false);
    }
}));


passport.serializeUser(function(user, cb) {
    process.nextTick(function() {
      cb(null, user);
    });
  });
  
  passport.deserializeUser(function(user, cb) {
    process.nextTick(function() {
      return cb(null, user);
    });
  });async function validateUser(email, password, user) {
    if (user == null) {
        throw new Error("User is null")
    } else {
        return Promise.resolve()
    }
}

export const loginController = async (req, res) => {
    try {
        const email = req.body.email, password = req.body.password;
        let user = await User.findOne({email: email})
        console.log(user._id.toString());
        
        await validateUser(email, password, user)
        const jwtBearerToken = jwt.sign({}, SECRET_KEY, {
            expiresIn: "365d",
            subject: user._id.toString()
        })

        res.cookie("SESSIONID", jwtBearerToken, {httpOnly:true});
        res.status(200).json({
            accessToken: jwtBearerToken,
            userId: user._id
        });
    } catch (err) {
        console.error(err)
        res.status(403).send();
    }
}