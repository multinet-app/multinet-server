<template>
  <v-dialog
    v-model="tableDialog"
    width="700"
  >
    <template v-slot:activator="{ on }">
      <v-btn
        id="add-table"
        class="new-button"
        color="blue darken-2"
        fab
        dark
        medium
        v-on="on"
      >
        <v-icon dark>add</v-icon>
      </v-btn>
    </template>
    <v-card>
      <v-card-title
        class="headline pb-0 pt-3"
        primary-title
      >
        Create Table
      </v-card-title>

      <v-card-text class="px-4 pt-4 pb-1">
        <v-layout wrap>
          <v-flex>
            <v-text-field
              id="table-name"
              autofocus
              filled
              v-model="newTable"
              label="Table name"
              :error-messages="tableCreationError"
            />
          </v-flex>
        </v-layout>
        <v-layout wrap>
          <v-flex
            class="pr-2"
            xs6
          >
            <v-file-input
              id="file-selector"
              clearable
              filled
              label="Upload file"
              prepend-icon=""
              prepend-inner-icon="attach_file"
              single-line
              @change="handleFileInput"
            />
          </v-flex>
          <v-flex
            class="pl-2"
            xs6
          >
            <v-select
              id="file-type"
              filled
              label="File type"
              v-if="typeList.length"
              v-model="selectedType"
              :items="typeList"
            />
          </v-flex>
        </v-layout>
      </v-card-text>

      <v-divider></v-divider>

      <v-card-actions class="px-4 py-3">
        <validation-errors :errors="errors" class="pr-3"></validation-errors>
        <v-spacer></v-spacer>
        <v-btn id="create-table" :disabled="tableCreateDisabled" @click="createTable">
          Create Table
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script lang="ts">
import { UploadType, ValidationError } from 'multinet';
import Vue from 'vue';

import api from '@/api';
import { FileTypeTable } from '@/types';

import ValidationErrors from '@/components/ValidationErrors.vue';

export default Vue.extend({
  name: 'TableDialog',

  props: {
    workspace: String,
  },
  components: {
    ValidationErrors,
  },
  data() {
    return {
      tableCreationError: null as string | null,
      tableDialog: false,
      selectedType: null as string | null,
      file: null as File | null,
      newTable: '',
      types: {
        csv: {extension: ['csv'], queryCall: 'csv'},
        newick: {extension: ['phy', 'tree'], queryCall: 'newick'},
        nested_json: {extension: ['json'], queryCall: 'nested_json'},
        d3_json: {extension: ['json'], queryCall: 'd3_json'},
      } as FileTypeTable,
      errors: [] as ValidationError[],
    };
  },

  computed: {
    typeList(): string[] {
      return Object.keys(this.types);
    },

    tableCreateDisabled(): boolean {
      return !this.file || !this.selectedType || !this.newTable;
    },
  },

  methods: {
    handleFileInput(file: File) {
      this.selectedType = this.fileType(file);
      this.file = file;
    },

    async createTable() {
      const queryType: UploadType = this.types[this.selectedType as string].queryCall;

      if (this.file === null) {
        // throw new Error('this.file must not be null');
        return;
      }

      try {
        await api.uploadTable(this.workspace, this.newTable, {
          type: queryType,
          data: this.file,
        });

        // this.tableCreationError = null;
        this.$emit('success');
        this.tableDialog = false;
      } catch (err) {
        // this.tableCreationError = err.response.data.message;
        this.errors = err.data.errors;
      }
    },

    fileType(file: File): string | null {
      if (!file) {
        return null;
      }

      const fileName = file.name.split('.');
      const extension = fileName[fileName.length - 1];

      for (const type in this.types) {
        if (this.types[type].extension.includes(extension)) {
          return type;
        }
      }
      return null;
    },

  },
});
</script>

<style scoped>
.new-button {
  margin: 49px 10px 0 0;
  z-index: 1;
}
</style>
