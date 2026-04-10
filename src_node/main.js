const { FlightRadar24API } = require("flightradarapi");
const frapi = new FlightRadar24API();
const path = require('path');
const express = require('express');
const app = express();
const nunjucks = require('nunjucks');
nunjucks.configure(path.join(__dirname, 'templates'), { express: app });

app.listen(3000, () => {
  console.log('Server running on port 3000');
});

app.use((req, res, next) => {
  console.log(`${new Date().toISOString()} ${req.method} ${req.url}`);
  next();
});

app.use('/static', express.static(path.join(__dirname, 'static')));

app.get('/', (req, res) => {
  res.render('index.html');
});
app.get('/airports', (req, res) => {
  res.render('airports.html');
});
app.get('/', (req, res) => {
  res.render('airport.html');
});