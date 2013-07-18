/*
 * index.js
 */

'use strict';

var childProcess = require('child_process'),
    fs = require('fs'),
    path = require('path');

var _ = require('lodash'),
    S = require('string'),
    async = require('async');

var PYTHON_SCRIPT_PATH = 'upload_video.py',
    CLIENT_SECRETS_PATH = 'client_secrets.json',
    OAUTH2_PATH = PYTHON_SCRIPT_PATH + '-oauth2.json';

function configure(config, cb) {
  if (!_.isObject(config)) { config = {}; }

  _.defaults(config, {
    accessToken: null,
    clientId: null,
    clientSecret: null,
    expiresIn: '3600',
    idToken: null,
    refreshToken: null,
    tokenType: 'Bearer'
  });

  async.parallel([
    function (cb) {
      fs.writeFile(
        path.join(__dirname, CLIENT_SECRETS_PATH),
        JSON.stringify({
          web: {
            'client_id': config.clientId,
            'client_secret': config.clientSecret,
            'redirect_uris': [],
            'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
            'token_uri': 'https://accounts.google.com/o/oauth2/token'
          }
        }, null, 2),
        cb
      );
    },
    function (cb) {
      fs.writeFile(
        path.join(__dirname, OAUTH2_PATH),
        JSON.stringify({
          '_module': 'oauth2client.client',
          'token_expiry': null,
          'access_token': config.accessToken,
          'token_uri': 'https://accounts.google.com/o/oauth2/token',
          'invalid': false,
          'token_response': {
            'access_token': config.accessToken,
            'token_type': config.tokenType,
            'expires_in': config.expiresIn
          },
          'client_id': config.clientId,
          'id_token': config.idToken,
          'client_secret': config.clientSecret,
          'revoke_uri': 'https://accounts.google.com/o/oauth2/revoke',
          '_class': 'OAuth2Credentials',
          'refresh_token': config.refreshToken,
          'user_agent': null
        }, null, 2),
        cb
      );
    }
  ], function (err) {
    cb(err);
  });
}

function upload(params, cb) {
  if (!_.isObject(params)) { params = {}; }

  _.defaults(params, {
    path: null,
    title: '',
    description: '',
    keywords: [],
    category: '22',  // People & Blogs
    privacy: 'private'
  });

  var child = childProcess.spawn('python', [
    PYTHON_SCRIPT_PATH,
    '--file', params.path,
    '--title', params.title,
    '--description', params.description,
    '--keywords', params.keywords.join(),
    '--category', params.category,
    '--privacyStatus', params.privacy
  ], { cwd: __dirname });

  var stdout = [],
      stderr = [];

  child.stdout.on('data', function (data) {
    stdout = stdout.concat(S(data).trim().s.split('\n'));
  });

  child.stderr.on('data', function (data) {
    stderr = stderr.concat(S(data).trim().s.split('\n'));
  });

  child.on('close', function (code) {
    if (code === 0) {
      return cb(null, _.last(stdout).match(/\(video id: (.+)\)/)[1]);
    } else {
      stderr.push('Exit code: ' + code);
      return cb(new Error(stderr));
    }
  });
}

// Public API
exports.configure = configure;
exports.upload = upload;
