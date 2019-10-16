import test from 'tape';
import process from 'process';

console.log(process.cwd());


import { multinetApi } from '../dist';


test('multinet test', (t) => {
  t.plan(2);

  t.ok(multinetApi, 'multinetApi() was imported successfully');
  t.equal(typeof multinetApi, 'function', 'multinetApi() is a function');
});
