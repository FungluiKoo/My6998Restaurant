'use strict';

function syncDelay(milliseconds){
  var start = new Date().getTime();
  var end = 0;

  while((end - start) < milliseconds){
      end = new Date().getTime();
  }
}

const yelp = require('yelp-fusion');

// Place holder for Yelp Fusion's API Key. Grab them
// from https://www.yelp.com/developers/v3/manage_app
const apiKey = '<apikey>';

async function myloop(){
  var counter = 0;
  for (let i = 0; i < 1000; i+=50) {
    const searchRequest = {
      limit: 50,
      offset: i,
      term:'Indian',
      location: 'New York, NY'
    };
    
    const client = yelp.client(apiKey);
    
    client.search(searchRequest).then(response => {
      const allResult = response.jsonBody.businesses;
      const prettyJson = JSON.stringify(allResult, null, 4);
      console.log(prettyJson);
      counter += allResult.length;
    }).catch(e => {
      console.log(e);
    });
    // console.log(counter);
    await new Promise(r=> setTimeout(r, 2000));
  }
}

myloop();