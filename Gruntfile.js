/*
 * Gruntfile.js
 */

'use strict';

module.exports = function (grunt) {
  // load all grunt tasks
  require('matchdep').filterDev('grunt-*').forEach(grunt.loadNpmTasks);

  // Project configuration.
  grunt.initConfig({
    jshint: {  // grunt-contrib-jshint
      options: {
        jshintrc: '.jshintrc'
      },
      all: [
        '**/*.js',
        '!node_modules/**/*'
      ]
    },
    watch: {  // grunt-regarde (task renamed from regarde to watch)
      all: {
        files: '**/*',
        tasks: 'jshint'
      }
    }
  });

  grunt.renameTask('regarde', 'watch');

  grunt.registerTask('default', [
    'jshint',
    'watch'
  ]);
};
