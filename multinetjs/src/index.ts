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

export type TableType = 'all' | 'node' | 'edge';

export type UploadType = 'csv' | 'nested_json' | 'newick';

export type Direction = 'all' | 'incoming' | 'outgoing';

export interface TablesOptionsSpec {
  type?: TableType;
}

export interface OffsetLimitSpec {
  offset?: number;
  limit?: number;
}

export type EdgesOptionsSpec = OffsetLimitSpec & {
  direction?: Direction;
}

export interface UploadTableOptionsSpec {
  type: UploadType;
  data: string | File;
}

export interface CreateGraphOptionsSpec {
  nodeTables: string[];
  edgeTable: string;
}function fileToText(file: File): Promise<string> {
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

  public tables(workspace: string, options: TablesOptionsSpec = {}): Promise<string[]> {
    return this.client.get(`workspaces/${workspace}/tables`, options);
  }

  public table(workspace: string, table: string, options: OffsetLimitSpec = {}): Promise<Array<{}>> {
    return this.client.get(`workspaces/${workspace}/tables/${table}`, options);
  }

  public graphs(workspace: string): Promise<string[]> {
    return this.client.get(`workspaces/${workspace}/graphs`);
  }

  public graph(workspace: string, graph: string): Promise<GraphSpec> {
    return this.client.get(`workspaces/${workspace}/graphs/${graph}`);
  }

  public nodes(workspace: string, graph: string, options: OffsetLimitSpec = {}): Promise<NodesSpec> {
    return this.client.get(`workspaces/${workspace}/graphs/${graph}/nodes`, options);
  }

  public attributes(workspace: string, graph: string, nodeId: string): Promise<{}> {
    return this.client.get(`workspaces/${workspace}/graphs/${graph}/nodes/${nodeId}/attributes`);
  }

  public edges(workspace: string, graph: string, nodeId: string, options: EdgesOptionsSpec = {}): Promise<EdgesSpec> {
    return this.client.get(`workspaces/${workspace}/graphs/${graph}/nodes/${nodeId}/edges`, options);
  }

  public createWorkspace(workspace: string): Promise<string> {
    return this.client.post(`/workspaces/${workspace}`);
  }

  public async uploadTable(workspace: string, table: string, { type, data }: UploadTableOptionsSpec): Promise<Array<{}>> {
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

  public createGraph(workspace: string, graph: string, { nodeTables, edgeTable }: CreateGraphOptionsSpec): Promise<string> {
    return this.client.post(`/workspaces/${workspace}/graph/${graph}`, {
      node_tables: nodeTables,
      edge_table: edgeTable,
    });
  }
}

export function multinetApi(baseURL: string): MultinetAPI {
  return new MultinetAPI(baseURL);
}
