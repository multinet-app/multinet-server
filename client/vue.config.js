const fs = require('fs');
const process = require('process');
const path = require('path');
const dotenv = require('dotenv');
const webpack = require('webpack');

const VuetifyLoaderPlugin = require('vuetify-loader/lib/plugin');

// Read in .env file.
const env = dotenv.parse(fs.readFileSync(path.resolve('..', '.env')));
process.env.FLASK_SERVE_PORT = process.env.FLASK_SERVE_PORT || env.FLASK_SERVE_PORT || 5000;

// Look for a git-sha file; if found, inject the value found in it into the
// application.
let GIT_SHA = null;
if (fs.existsSync('git-sha')) {
  GIT_SHA = JSON.stringify(fs.readFileSync('git-sha').toString().trim());
}

// Inject a value for gaTag (google analytics) if present as well.
let GA_TAG = null;
if (fs.existsSync('ga-tag')) {
  GA_TAG = JSON.stringify(fs.readFileSync('ga-tag').toString().trim());
}

module.exports = {
  configureWebpack: {
    plugins: [
      new VuetifyLoaderPlugin(),
      new webpack.DefinePlugin({
        GIT_SHA,
        GA_TAG,
      }),
    ],
  },
  devServer: {
    proxy: {
      '/api': {
        target: `http://127.0.0.1:${process.env.FLASK_SERVE_PORT}/api`,
        changeOrigin: true,
        pathRewrite: {
          '^/api': '',
        },
      }
    }
  }
};
