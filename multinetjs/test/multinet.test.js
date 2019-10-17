import test from 'tape';
import process from 'process';

import { multinetApi } from '../dist';

test('multinet test', async (t) => {
  t.ok(multinetApi, 'multinetApi() was imported successfully');
  t.equal(typeof multinetApi, 'function', 'multinetApi() is a function');

  const api = multinetApi('http://localhost:50000/api');
  t.ok(api, 'multinetApi() gave us an API object');

  try {
    const workspaces = await api.workspaces();
    t.deepEqual(workspaces, [], 'new server should have no workspaces');
  } catch(e) {
    t.fail(`api.workspaces() failed: ${e.status} ${e.statusText}`);
  }

  t.end();
});
