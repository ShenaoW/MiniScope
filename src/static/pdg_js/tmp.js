"use strict";

function _typeof(obj) { "@babel/helpers - typeof"; return _typeof = "function" == typeof Symbol && "symbol" == typeof Symbol.iterator ? function (obj) { return typeof obj; } : function (obj) { return obj && "function" == typeof Symbol && obj.constructor === Symbol && obj !== Symbol.prototype ? "symbol" : typeof obj; }, _typeof(obj); }
function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }
function _defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, _toPropertyKey(descriptor.key), descriptor); } }
function _createClass(Constructor, protoProps, staticProps) { if (protoProps) _defineProperties(Constructor.prototype, protoProps); if (staticProps) _defineProperties(Constructor, staticProps); Object.defineProperty(Constructor, "prototype", { writable: false }); return Constructor; }
function _toPropertyKey(arg) { var key = _toPrimitive(arg, "string"); return _typeof(key) === "symbol" ? key : String(key); }
function _toPrimitive(input, hint) { if (_typeof(input) !== "object" || input === null) return input; var prim = input[Symbol.toPrimitive]; if (prim !== undefined) { var res = prim.call(input, hint || "default"); if (_typeof(res) !== "object") return res; throw new TypeError("@@toPrimitive must return a primitive value."); } return (hint === "string" ? String : Number)(input); }
// Example code using multiple ES6 features

// let and const for variable declarations
var myVar = "hello";
var myConst = "world";

// Arrow function
var sum = function sum(a, b) {
  return a + b;
};
console.log(sum(2, 3)); // Output: 5

// Template literals
console.log("The value of myVar is ".concat(myVar));

// Spread operator
var myArray = [1, 2, 3];
var myOtherArray = [4, 5, 6];
var mergedArray = [].concat(myArray, myOtherArray);
console.log(mergedArray); // Output: [1, 2, 3, 4, 5, 6]

// Destructuring assignment
var myObj = {
  name: "John",
  age: 30
};
var name = myObj.name,
  age = myObj.age;
console.log("My name is ".concat(name, " and I'm ").concat(age, " years old"));

// Classes
var Person = /*#__PURE__*/function () {
  function Person(name, age) {
    _classCallCheck(this, Person);
    this.name = name;
    this.age = age;
  }
  _createClass(Person, [{
    key: "sayHello",
    value: function sayHello() {
      console.log("Hello, my name is ".concat(this.name));
    }
  }]);
  return Person;
}();
var john = new Person("John", 30);
john.sayHello();