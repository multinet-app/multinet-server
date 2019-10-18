import fs from 'fs';
import test from 'tape';
import process from 'process';

import { multinetApi } from '../dist';

const membersText = fs.readFileSync('../test/data/members.csv', 'utf8');
const clubsText = fs.readFileSync('../test/data/clubs.csv', 'utf8');
const membershipText = fs.readFileSync('../test/data/membership.csv', 'utf8');

function failMessage(call, exc) {
  return `${call} failed: ${exc.status} ${exc.statusText}`;
}

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

  const newWorkspace = 'foobar';
  try {
    const result = await api.createWorkspace(newWorkspace);
    t.equal(result, newWorkspace, 'created new workspace "foobar"');
  } catch(e) {
    t.fail(`api.createWorkspace() failed: ${e.status} ${e.statusText}`);
  }

  try {
    const workspaces = await api.workspaces();
    t.deepEqual(workspaces, ['foobar'], 'after creating workspace, server has it');
  } catch(e) {
    t.fail(`api.workspaces() failed: ${e.status} ${e.statusText}`);
  }

  try {
    const foobarWS = await api.workspace(newWorkspace);
    const expected = {
      name: 'foobar',
      owner: '',
      readers: [],
      writers: [],
    };

    t.deepEqual(foobarWS, expected, 'retrieving new workspace works correctly');
  } catch(e) {
    t.fail(failMessage(`api.workspace("${newWorkspace}")`, e));
  }

  try {
    const tables = await api.tables(newWorkspace);
    t.deepEqual(tables, [], 'new workspace should have no tables');
  } catch(e) {
    t.fail(failMessage(`api.tables("${newWorkspace}")`, e));
  }

  try {
    const result = await api.uploadTable('csv', newWorkspace, 'members', membersText);
    t.deepEqual(result, { count: 254 }, 'server reports the correct number of lines added to database');
  } catch(e) {
    t.fail(failMessage('api.uploadTable()', e));
  }

  try {
    const tables = await api.tables(newWorkspace);
    t.deepEqual(tables, ['members'], 'after adding a table, workspace should have it');
  } catch(e) {
    t.fail(failMessage(`api.tables("${newWorkspace}")`, e));
  }

  try {
    let members = await api.table(newWorkspace, 'members');
    t.equal(members.length, 30, 'asking for table yields 30 items');

    members = await api.table(newWorkspace, 'members', 0, 50);
    t.equal(members.length, 50, 'asking table for 50 items yields 50 items');

    members = await api.table(newWorkspace, 'members', 0, 254);
    t.equal(members.length, 254, 'asking table for all items yields 254 items');

    members = await api.table(newWorkspace, 'members', 0, 300);
    t.equal(members.length, 254, 'asking table for more than 254 items yields 254 items');
  } catch(e) {
    t.fail(failMessage(`api.table("${newWorkspace}", "members")`, e));
  }

  try {
    let result = await api.uploadTable('csv', newWorkspace, 'clubs', clubsText);
    t.deepEqual(result, { count: 7 }, 'upload clubs data');

    result = await api.uploadTable('csv', newWorkspace, 'membership', membershipText);
    t.deepEqual(result, { count: 319 }, 'upload membership data');

    result = await api.tables(newWorkspace);
  } catch(e) {
    t.fail(failMessage('api.uploadTable()', e));
  }

  try {
    let result = await api.createGraph(newWorkspace, 'boston', ['clubs', 'members'], 'membership');
    t.equal(result, 'boston', 'boston graph created successfully');
  } catch(e) {
    t.fail(failMessage(`api.createGraph("${newWorkspace}", "boston", ["clubs", "members"], "membership")`, e));
  }

  try {
    result = await api.createGraph(newWorkspace, 'boston', ['clubs', 'members'], 'membership');
    t.fail('creating an existing graph results should not be successful');

  } catch(e) {
    t.ok(e.status === 409 && e.statusText === 'Graph Already Exists', 'creating an existing graph results in 409 error');
  }

  try {
    const graph = await api.graph(newWorkspace, 'boston');
    t.equal(graph.edgeTable, 'membership', 'graph has correct edge table');
    t.deepEqual(graph.nodeTables, ['clubs', 'members'], 'graph has correct node tables');
  } catch(e) {
    t.fail(failMessage(`api.graph("${newWorkspace}", "boston"`, e));
  }

  try {
    let nodes = await api.nodes(newWorkspace, 'boston');
    t.equal(nodes.count, 261, 'graph has correct number of reported nodes');
    t.equal(nodes.nodes.length, 30, 'asking for graph nodes yields 30 items');

    nodes = await api.nodes(newWorkspace, 'boston', 0, 50);
    t.equal(nodes.nodes.length, 50, 'asking for graph nodes yields 50 items');

    nodes = await api.nodes(newWorkspace, 'boston', 0, 261);
    t.equal(nodes.nodes.length, 261, 'asking for all graph nodes yields 261 items');

    nodes = await api.nodes(newWorkspace, 'boston', 0, 300);
    t.equal(nodes.nodes.length, 261, 'asking for more than all graph nodes yields 261 items');
  } catch(e) {
    t.fail(failMessage(`api.nodes("${newWorkspace}", "boston", ...)`, e));
  }

  try {
    const attrs = await api.attributes(newWorkspace, 'boston', 'clubs/0');
    t.deepEqual(attrs, {_key: '0', _id: 'clubs/0', name: 'St Andrews Lodge'}, 'correct attributes come back for node');
  } catch(e) {
    t.fail(failMessage(`api.attributes("${newWorkspace}", "boston", "clubs/0"`, e));
  }

  try {
    let edges = await api.edges(newWorkspace, 'boston', 'clubs/0', 'all');
    t.equal(edges.count, 53, 'correct number of total edges reported');
    t.equal(edges.edges.length, 30, 'correct number of edges sent back');

    edges = await api.edges(newWorkspace, 'boston', 'clubs/0', 'outgoing');
    t.equal(edges.count, 0, 'correct number of total outgoing edges reported');
    t.equal(edges.edges.length, 0, 'correct number of outgoing edges sent back');

    edges = await api.edges(newWorkspace, 'boston', 'clubs/0', 'incoming');
    t.equal(edges.count, 53, 'correct number of total incoming edges reported');
    t.equal(edges.edges.length, 30, 'correct number of incoming edges sent back');

  } catch(e) {
    t.fail(failMessage(``, e));
  }

  t.end();
});
