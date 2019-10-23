import { Client } from './client';

export interface GraphSpec {
  edgeTable: string;
  nodeTables: string[];
}

export interface NodesSpec {
  count: number;
  nodes: string[];
}

export interface Edge {
  edge: string;
  from: string;
  to: string;
}

export interface EdgesSpec {
  count: number;
  edges: Edge[];
}

export type TableType = 'csv' | 'nested_json' | 'newick';

export type Direction = 'all' | 'incoming' | 'outgoing';

function fileToText(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      if (e.target === null || typeof e.target.result !== 'string') {
        throw new Error();
      }
      resolve(e.target.result);
    };
    reader.onerror = (e) => {
      reject();
    };

    reader.readAsText(file);
  });
}

class MultinetAPI {
  private client: Client;

  constructor(baseURL: string) {
    this.client = new Client(baseURL);
  }

  public workspaces(): Promise<string[]> {
    return this.client.get('workspaces');
  }

  public workspace(workspace: string): Promise<string> {
    if (!workspace) {
      throw new Error('argument "workspace" must not be empty');
    }

    return this.client.get(`workspaces/${workspace}`);
  }

  public tables(workspace: string): Promise<string[]> {
    return this.client.get(`workspaces/${workspace}/tables`);
  }

  public table(workspace: string, table: string, offset: number = 0, limit: number = 30): Promise<Array<{}>> {
    return this.client.get(`workspaces/${workspace}/tables/${table}`, {
      offset,
      limit,
    });
  }

  public graphs(workspace: string): Promise<string[]> {
    return this.client.get(`workspaces/${workspace}/graphs`);
  }

  public graph(workspace: string, graph: string): Promise<GraphSpec> {
    return this.client.get(`workspaces/${workspace}/graphs/${graph}`);
  }

  public nodes(workspace: string, graph: string, offset: number = 0, limit: number = 30): Promise<NodesSpec> {
    return this.client.get(`workspaces/${workspace}/graphs/${graph}/nodes`, {
      offset,
      limit,
    });
  }

  public attributes(workspace: string, graph: string, nodeId: string): Promise<{}> {
    return this.client.get(`workspaces/${workspace}/graphs/${graph}/nodes/${nodeId}/attributes`);
  }

  public edges(
      workspace: string,
      graph: string,
      nodeId: string,
      direction: Direction = 'all',
      offset: number = 0,
      limit: number = 30): Promise<EdgesSpec> {
    return this.client.get(`workspaces/${workspace}/graphs/${graph}/nodes/${nodeId}/edges`, {
      direction,
      offset,
      limit,
    });
  }

  public createWorkspace(workspace: string): Promise<string> {
    return this.client.post(`/workspaces/${workspace}`);
  }

  public async uploadTable(type: TableType, workspace: string, table: string, data: string | File): Promise<Array<{}>> {
    let text;
    if (typeof data === "string") {
      text = data;
    } else {
      text = await fileToText(data);
    }

    return this.client.post(`/${type}/${workspace}/${table}`, text, {
      'Content-Type': 'text/plain',
    });
  }

  public createGraph(workspace: string, graph: string, nodeTables: string[], edgeTable: string): Promise<string> {
    return this.client.post(`/workspaces/${workspace}/graph/${graph}`, {
      node_tables: nodeTables,
      edge_table: edgeTable,
    });
  }
}

export function multinetApi(baseURL: string): MultinetAPI {
  return new MultinetAPI(baseURL);
}
