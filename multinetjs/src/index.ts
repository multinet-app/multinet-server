export function add(x: number, y: number): number {
  return x + y + 3.1;
}

export function sub(x: number, y: number) {
  return x - y;
}

export const pi = 3.14;

function timeout(ms: number) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export async function waitandsay(msg: string, delay: number) {
  await timeout(delay);
  console.log(msg);
}
