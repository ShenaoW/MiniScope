module.exports = {
    frm6to5: frm6to5,
};

let babel = require("@babel/core");
let fs = require("fs");
let process = require("process");


function frm6to5(filename) {
    let es6Code = fs.readFileSync(filename).toString('utf-8');
    const options = {
        filename: filename,
        presets: [
            ['@babel/preset-env', { targets: 'defaults' }],
            '@babel/preset-typescript',
        ],
    };
    try {
        var result = babel.transformSync(es6Code, options);
    } catch(e) {
        console.error(filename, e);
        process.exit(1);
    }
    let es5Code = result["code"]
    fs.writeFile(filename, es5Code, function (err) {
        if (err) {
            console.error(err);
        }
    });

    return es5Code;
}

frm6to5(process.argv[2]);
