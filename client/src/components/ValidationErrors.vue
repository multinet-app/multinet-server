<template>
  <v-expansion-panels>
    <v-expansion-panel
      v-for="(item, i) in errors"
      :key="i"
    >
      <v-expansion-panel-header class="red lighten-2">{{item.type}}</v-expansion-panel-header>
      <v-expansion-panel-content class="red lighten-2">{{JSON.stringify(withoutTypes[i], null, 2)}}</v-expansion-panel-content>
    </v-expansion-panel>
  </v-expansion-panels>
</template>

<script lang="ts">
import Vue, { PropType } from 'vue';
import { ValidationError } from 'multinet';

interface VueTreeView {
  id?: number;
  name: string;
  children?: VueTreeView[];
}

type BasicType = string | number;

interface ObjectType {
  [key: string]: BasicType | ObjectType;
}


export default Vue.extend({
  name: 'ValidationErrors',
  props: {
    errors: Array as PropType<ValidationError[]>,
  },
  computed: {
    withoutTypes(): any[] {
      return this.errors.map((err) => (
        Object.keys(err)
        .filter((key) => key !== 'type')
        .reduce((obj, key) => ({...obj, [key]: err[key]}), {})
      ));
    },
  },
  methods: {},
});
</script>

<style>
</style>
