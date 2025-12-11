const express = require('express');
const router = express.Router();

const homo = require("../lib/homo");

// /api/homo
router.get('/homo', (req, res) => {
    try{
        const input = req.query.input;
        if (!input) {
            res.send("「input」引数が必要です。");
            return;
        }

        const num = Number.parseInt(input);
        if (num > 99999) {
            res.send("数字が大きすぎます。");
            return;
        }
        const int = homo(num);
        res.send(`${int}`);
    } catch (e) {
        res.send("エラーが発生しました。引数がないかもです。");
        return;
    }
});

module.exports = router;