import axios, { AxiosInstance } from 'axios';

class Client {
  axios: AxiosInstance;

  constructor(baseURL: string) {
    this.axios = axios.create({
      baseURL,
    });
  }

  get(path: string): Promise<string[]> {
    return new Promise((resolve, reject) => {
      this.axios.get(path)
        .then(resp => {
          resolve(resp.data);
        })
        .catch(resp => {
          reject(resp.response);
        });
    });
  }
}

class MultinetAPI {
  client: Client;

  constructor(baseURL: string) {
    this.client = new Client(baseURL);
  }

  workspaces(): Promise<string[]> {
    return this.client.get('workspaces');
  }

  workspace(workspace: string): Promise<any> {
    if (!workspace) {
      throw new Error('argument "workspace" must not be empty');
    }

    return this.client.get(`workspaces/${workspace}`);
  }

  tables(workspace: string): Promise<any> {
    return this.client.get(`workspaces/${workspace}/tables`);
  }

  table(workspace: string, table: string, offset: int = 0, limit: int = 30): Promise<any> {
    return this.client.get(`workspaces/${workspace}/tables/${table}`, {
      offset,
      limit,
    });
  }

  graphs(workspace: string): Promise<any> {
    return this.client.get(`workspaces/${workspace}/graphs`);
  }

  graph(workspace: string, graph: string): Promise<any> {
    return this.client.get(`workspaces/${workspace}/graphs/${graph}`);
  }

  nodes(workspace: string, graph: string, offset: int = 0, limit: int = 30): Promise<any> {
    return this.client.get(`workspaces/${workspace}/graphs/${graph}/nodes`, {
      offset,
      limit,
    });
  }

  attributes(workspace: string, graph: string, nodeId: string): Promise<any> {
    return this.client.get(`workspaces/${workspace}/graphs/${graph}/${nodeId}/attributes`);
  }

  edges(workspace: string, graph: string, nodeId: string, direction: string = 'all', offset: int = 0, limit: int = 30) {
    return this.client.get(`workspaces/${workspace}/graphs/${graph}/${nodeId}/edges`, {
      direction,
      offset,
      limit,
    });
  }
}

export function multinetApi(baseURL: string) {
  return new MultinetAPI(baseURL);
}
