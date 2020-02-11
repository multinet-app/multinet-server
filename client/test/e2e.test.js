import test from 'tape';
import puppeteer from 'puppeteer';

const width = 1920;
const height = 1080;

// Opens the chromium window
function browser(width, height) {
  return puppeteer.launch({
    headless: true,
    args: [`--window-size=${width},${height}`],
    // slowMo: 20 // For testing
  });
}

// Sets up the browser with some default settings
async function setup() {
  const b = await browser(width, height);
  const p = await b.newPage();
  await p.setViewport({ width, height });
  await p.goto('http://127.0.0.1:8080/');
  await p.setDefaultTimeout(5000);
  return [b, p];
}

// Converts throwing behavior of waitForSelector() into a return value.
function waitForSelector(p, selector) {
  try {
    return p.waitForSelector(selector);
  } catch (e) {
    return Promise.resolve(null);
  }
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Clicks the add workspace button, types a name, and clicks the button
async function create_workspace(p, name) {
  let found = await waitForSelector(p, '#add-workspace');
  if (!found) {
    return false;
  }

  await p.click('#add-workspace');

  await sleep(500);

  found = await waitForSelector(p, '#workspace-name');
  if (!found) {
    return false;
  }

  await p.focus('#workspace-name');
  await p.keyboard.type(name);
  await p.click('#create-workspace');

  return true;
}

// Checks that a workspace exists in the left pane
async function workspace_exists(p, name) {
  let exists = false;

  const found = await waitForSelector(p, '.v-list-item__title');
  if (!found) {
    return null;
  }

  let workspaces = await p.evaluate(() => {
    let titles = [];
    let doc_nodes = document.querySelectorAll('.v-list-item__title');
    for (let node of doc_nodes) {
      titles.push(node.innerText);
    }
    return titles;
  });

  exists = workspaces.includes(name);
  return exists;
}

// Get the names of either all tables or all graphs in the current workspace
async function get_element_names(element_type, p) {
  let tables;

  // Search for the text of the table or graph elements
  const found = await waitForSelector(p, `[data-title="${element_type}"] .ws-detail-empty-list`);
  if (!found) {
    return null;
  }

  tables = await p.evaluate(element_type => {
    let titles = [];
    let doc_nodes = document.querySelectorAll(`[data-title="${element_type}"] .ws-detail-empty-list`);
    for (let node of doc_nodes) {
      titles.push(node.innerText);
    }
    return titles;
  }, element_type);

  return tables;
}

// Checks if a table or graph exists in the current workspace
async function element_exists(element_type, p, name) {
  let exists, tables;

  tables = await get_element_names(element_type, p);
  if (tables === null) {
    return null;
  }

  exists = tables.includes(name);
  return exists;
}

// Checks if no tables or graphs exist in the current workspace
async function elements_empty(element_type, p) {
  let list_is_empty, tables;

  tables = await get_element_names(element_type, p);
  if (tables === null) {
    return null;
  }

  list_is_empty = tables.includes('info There\'s nothing here yet...');
  return list_is_empty;
}


// Start of tests
test('e2e - Check that actions that should work, do work', async (t) => {
  // Arrange: Set up the page
  const [b, p] = await setup();

  // Click once on the "got it" button.
  await sleep(500);
  p.click('#got-it');
  await sleep(500);

  // Act: Test creating a workspace
  if (!await create_workspace(p, 'puppeteer')) {
    t.fail('Could not create workspace');
    t.end();
    return;
  }

  await sleep(500);

  // Assert: Check that the new workspace exists with no tables
  let exists = await workspace_exists(p, 'puppeteer');
  if (exists === null) {
    t.fail('Could not check for workspace');
    t.end();
    return;
  }
  t.ok(exists, 'Workspace called "puppeteer" was created.');

  // Assert: Check that there are no tables or graphs yet
  exists = await elements_empty('Tables', p, undefined);
  if (exists === null) {
    t.fail('Could not check for empty element');
    t.end();
    return;
  }

  t.ok(exists, 'The new workspace has no tables.');

  exists = await elements_empty('Networks', p, undefined);
  t.ok(exists, 'The new workspace has no networks.');

  // Cleanup
  await b.close();
  t.end();
});

test('e2e - Check that actions that shouldn\'t work, don\'t work', async (t) => {
  // Arrange: Set up the page
  const [b, p] = await setup();

  // Click once on the "got it" button.
  await sleep(500);
  p.click('#got-it');
  await sleep(500);

  // Act: Test creating invalid workspaces
  await create_workspace(p, '123');

  await sleep(500);

  await p.click('#workspace-name', { clickCount: 3 });
  await p.click('#add-workspace'); // Close the modal (this will cause a failure in the next command if it is made)
  await sleep(500);

  await create_workspace(p, '++--==__');
  await p.click('#workspace-name', { clickCount: 3 });
  await p.click('#add-workspace'); // Close the modal (this will cause a failure in the next command if it is made)
  await sleep(500);

  await create_workspace(p, 'a');

  // Assert: Check that the new workspace exists with no tables
  await sleep(200);
  let exists = await workspace_exists(p, '123');
  t.notOk(exists, 'Workspace called "123" wasn\'t created.');

  exists = await workspace_exists(p, '++--==__');
  t.notOk(exists, 'Workspace called "++--==__" wasn\'t created.');

  exists = await workspace_exists(p, 'a');
  t.ok(exists, 'Workspace called "a" was created.');

  exists = await element_exists('Tables', p, 'broken');
  if (exists === null) {
    t.fail('Could not check for element existence');
    t.end();
    return;
  }
  t.notOk(exists, 'New workspaces don\'t have tables');

  // Cleanup
  await b.close();
  t.end();
});
