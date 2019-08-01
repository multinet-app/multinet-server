import React from 'react';
import ReactDOM from 'react-dom';
import GraphiQL from 'graphiql';
import fetch from 'isomorphic-fetch';

import 'graphiql/graphiql.css';

const HOST = 'http://localhost:9090';

function graphQLFetcher(graphQLParams) {
  console.log(graphQLParams);

  const json = JSON.stringify({
    'query': graphQLParams.query,
    'variables': graphQLParams.variables
  });

  return fetch(`${HOST}/api/multinet/graphql`, {
    method: 'post',
    headers: {
      'Content-Type': 'application/json',
    },
    body: json,
  }).then(response => response.json());
}

// Use a 500ms timeout to avoid a problem of the actual query editor being
// hidden otherwise (see
// https://github.com/graphql/graphiql/issues/770#issuecomment-505699802).
window.setTimeout(() => {
  ReactDOM.render(
    <div style={{ height: '100vh' }}>
      <GraphiQL fetcher={graphQLFetcher} />
    </div>, document.body);
}, 500);
