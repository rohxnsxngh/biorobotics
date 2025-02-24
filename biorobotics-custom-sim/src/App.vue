<script setup lang="ts"></script>

<template>
  <div><Undulation /></div>
</template>

<script>
import { defineComponent } from "vue";
import Undulation from "./components/Undulation.vue";

export default defineComponent({
  name: "App",
  components: {
    Undulation,
  },
});
</script>
