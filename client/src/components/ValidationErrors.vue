<template>
  <v-treeview dense :items="errorTree" open-on-click :openall="false" color="red" rounded></v-treeview>
</template>

<script lang="ts">
import Vue, { PropType } from "vue";
import { ValidationError, NoBodyError } from "multinet";

interface VueTreeView {
  id?: number;
  name: string;
  children?: VueTreeView[];
}

type BasicType = string | number;

interface ObjectType {
  [key: string]: BasicType | ObjectType;
}

function noErrorBody(err: ValidationError): err is NoBodyError {
  return !('body' in err);
}


export default Vue.extend({
  name: 'ValidationErrors',
  props: {
    errors: Array as PropType<ValidationError[]>,
  },
  computed: {
    errorTree(): VueTreeView[] {
      return this.errors.map((x: ValidationError) => ({
        name: x.type,
        children: noErrorBody(x) ? [] : this.toTreeRecursive(x.body),
      }));
    },
  },
  methods: {
    toTreeRecursive(node: ObjectType): VueTreeView[] {
      const array = Object.keys(node).map((key) => {
        if (node[key] instanceof Object) {
          return {
            name: key,
            children: this.toTreeRecursive(node[key])
          };
        }

        let name;
        if (!isNaN(Number(key))) {
          name = node[key];
        } else {
          name = `${key}: ${node[key]}`;
        }

        return { name };
      });

      return array;
    },
  },
});
</script>

<style>
</style>
