<template>
  <v-app>
    <v-app-bar color="surface" elevation="1" height="76">
      <v-container class="d-flex align-center" style="height: 100%;">
        <img :src="logo" alt="Tribunal de Contas do Município do Rio de Janeiro" height="30" />
        <v-divider vertical class="mx-4" style="height: 30px;" />
        <div class="d-flex flex-column" style="line-height: 1.25;">
          <span
            class="text-caption font-weight-bold"
            style="letter-spacing: 0.08em; color: #092F57;"
          >1ª IGE · SGCE</span>
          <span
            class="text-caption"
            style="letter-spacing: 0.05em; color: #3896B4;"
          >PPP MATURITY CHECK SYSTEM</span>
        </div>
      </v-container>
    </v-app-bar>

    <v-main>
      <router-view />
    </v-main>
  </v-app>
</template>

<script setup>
import logo from './assets/logo_tcmrio_horizontal.png'
</script>
