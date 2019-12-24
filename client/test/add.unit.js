import test from 'tape';

import { add } from '../src/func';

test('add function works', (t) => {
  t.equal(10, add(4, 6), '4 + 6 === 10');
  t.end();
});
