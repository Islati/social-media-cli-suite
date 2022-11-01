<template>
  <v-app>
    <v-app-bar>
      <v-app-bar-title @click="$router.push('/')" class="mx-2">
        <v-icon>mdi-bomb</v-icon>
        Skreet <small class="text-grey-lighten-1">(Admin)</small>
      </v-app-bar-title>
      <v-btn to="/feed-importer" class="float-left" variant="plain">
        <v-icon>mdi-reddit</v-icon>
        <span class="text-center">Reddit Feed Importer</span>
      </v-btn>


<!--      <v-btn to="/calendar" class="mx-2">-->
<!--        <v-icon>mdi-calendar</v-icon>-->
<!--        <span class="text-center">Post Calendar</span>-->
<!--      </v-btn>-->

      <v-spacer></v-spacer>
    </v-app-bar>
    <v-main>
      <router-view></router-view>
    </v-main>
  </v-app>
</template>

<script>

export default {
  name: 'App',

  components: {},

  data: () => ({
    //
  }),
}
</script>
