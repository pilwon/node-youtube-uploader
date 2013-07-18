/*
 * index.js
 */

'use strict';

var path = require('path');

var _ = require('lodash');

// Add `python_modules` to PYTHONPATH.
var pythonModulesPath = path.join(__dirname, 'python_modules') + '/',
    pythonPath = process.env.PYTHONPATH.split(':').concat(pythonModulesPath);
process.env.PYTHONPATH = _.compact(pythonPath).join(':') + ':';

exports = module.exports = require('./lib');
