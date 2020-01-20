export interface NoBodyError {
    type: 'csv_unsupported_table' | 'd3_invalid_structure' | 'd3_invalid_link_keys' | 'd3_inconsistent_link_keys' | 'd3_node_duplicates';
}

export interface BasicError {
    type: 'graph_creation_undefined_tables' | 'csv_duplicated_keys' | 'newick_duplicate_keys';
    body: string[];
}

export interface GraphUndefinedKeys {
    type: 'graph_creation_undefined_keys';
    body: {
        table: string,
        keys: string[]
    };
}

export interface CSVInvalidSyntax {
    type: 'csv_invalid_syntax';
    body: [
        {
            row: number,
            fields: string[]
        }
    ];
}

export interface NewickDuplicateEdges {
    type: 'newick_duplicate_edges';
    body: [
        {
            _from: string,
            _to: string,
            length: number
        }
    ];
}




export type ValidationError = NoBodyError | BasicError | GraphUndefinedKeys | CSVInvalidSyntax | NewickDuplicateEdges;

