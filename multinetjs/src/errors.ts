export interface D3InvalidStructure {
    type: 'D3InvalidStructure';
}

export interface D3InvalidLinkKeys {
    type: 'D3InvalidLinkKeys';
}

export interface D3InconsistentLinkKeys {
    type: 'D3InconsistentLinkKeys';
}

export interface D3NodeDuplicates {
    type: 'D3NodeDuplicates';
}


export interface UnsupportedTable {
    type: 'UnsupportedTable';
}

export interface DuplicateKey {
    type: 'DuplicateKey';
    key: string;
}

export interface GraphCreationUndefinedTables {
    type: 'GraphCreationUndefinedTables';
    table: string;
}

export interface GraphCreationUndefinedKeys {
    type: 'GraphCreationUndefinedKeys';
    table: string;
    keys: string[];
}

export interface CsvInvalidRow {
    type: 'CsvInvalidRow';
    row: number;
    fields: string[];
}

export interface NewickDuplicateEdge {
    type: 'NewickDuplicateEdge';
    _from: string;
    _to: string;
    length: number;
}

export type ValidationError = D3InconsistentLinkKeys
    | D3InvalidLinkKeys
    | D3NodeDuplicates
    | D3InvalidStructure
    | UnsupportedTable
    | DuplicateKey
    | GraphCreationUndefinedTables
    | GraphCreationUndefinedKeys
    | CsvInvalidRow
    | NewickDuplicateEdge;
