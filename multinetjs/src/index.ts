import axios, { AxiosInstance } from 'axios';

class Client {
  axios: AxiosInstance;

  constructor(baseURL: string) {
    this.axios = axios.create({
      baseURL,
    });
  }

  get(path: string, params: {} = {}): Promise<any> {
    return new Promise((resolve, reject) => {
      this.axios.get(path, { params, })
        .then(resp => {
          resolve(resp.data);
        })
        .catch(resp => {
          reject(resp.response);
        });
    });
  }

  post(path: string, params: {} = {}, headers: {} = {}): Promise<any> {
    return new Promise((resolve, reject) => {
      this.axios.post(path, params, { headers, })
        .then(resp => {
          resolve(resp.data);
        })
        .catch(resp => {
          reject(resp.response);
        });
    });
  }
}

export interface GraphSpec {
  edgeTable: string;
  nodeTables: string[];
}

export interface NodesSpec {
  count: number;
  nodes: string[];
}

export interface EdgesSpec {
  count: number;
  edges: string[];
}

class MultinetAPI {
  client: Client;

  constructor(baseURL: string) {
    this.client = new Client(baseURL);
  }

  workspaces(): Promise<string[]> {
    return this.client.get('workspaces');
  }

  workspace(workspace: string): Promise<string> {
    if (!workspace) {
      throw new Error('argument "workspace" must not be empty');
    }

    return this.client.get(`workspaces/${workspace}`);
  }

  tables(workspace: string): Promise<string[]> {
    return this.client.get(`workspaces/${workspace}/tables`);
  }

  table(workspace: string, table: string, offset: number = 0, limit: number = 30): Promise<{}[]> {
    return this.client.get(`workspaces/${workspace}/tables/${table}`, {
      offset,
      limit,
    });
  }

  graphs(workspace: string): Promise<string[]> {
    return this.client.get(`workspaces/${workspace}/graphs`);
  }

  graph(workspace: string, graph: string): Promise<GraphSpec> {
    return this.client.get(`workspaces/${workspace}/graphs/${graph}`);
  }

  nodes(workspace: string, graph: string, offset: number = 0, limit: number = 30): Promise<NodesSpec> {
    return this.client.get(`workspaces/${workspace}/graphs/${graph}/nodes`, {
      offset,
      limit,
    });
  }

  attributes(workspace: string, graph: string, nodeId: string): Promise<{}> {
    return this.client.get(`workspaces/${workspace}/graphs/${graph}/nodes/${nodeId}/attributes`);
  }

  edges(workspace: string, graph: string, nodeId: string, direction: string = 'all', offset: number = 0, limit: number = 30): Promise<EdgesSpec> {
    return this.client.get(`workspaces/${workspace}/graphs/${graph}/nodes/${nodeId}/edges`, {
      direction,
      offset,
      limit,
    });
  }

  createWorkspace(workspace: string): Promise<string> {
    return this.client.post(`/workspaces/${workspace}`);
  }

  uploadTable(type: 'csv' | 'nested_json' | 'newick', workspace: string, table: string, data: string): Promise<{}[]> {
    return this.client.post(`/${type}/${workspace}/${table}`, data, {
      'Content-Type': 'text/plain',
    });
  }

  createGraph(workspace: string, graph: string, nodeTables: string[], edgeTable: string): Promise<string> {
    return this.client.post(`/workspaces/${workspace}/graph/${graph}`, {
      node_tables: nodeTables,
      edge_table: edgeTable,
    });
  }
}

export function multinetApi(baseURL: string): MultinetAPI {
  return new MultinetAPI(baseURL);
}
