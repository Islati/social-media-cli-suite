<template>
  <v-container class="mt-3">
    <v-row dense>
      <h4>Feed Importer</h4>
    </v-row>
    <!--    Subreddit Feed Load -->

    <!--    Todo Implement grid based feed importer,
                  with images having modal popover
                  to schedule the posts & allow multiple
                  sources to be easily shown in one place.
    -->
    <v-form ref="form">
      <v-row>
        <v-col cols="3">
          <v-text-field
              v-model="feedSubreddit"
              label="Subreddit"
              required
              id="feedSubreddit"
          ></v-text-field>
        </v-col>
        <v-col cols="2">
          <v-select v-model="feedSortType" id="feedSortTypeSelect" :items="sortTypes" label="Sort by.."
                    item-text="sortType"></v-select>
        </v-col>

        <v-btn @click="loadSubredditFeed" color="success" class="mt-5">
          <v-icon>mdi-refresh</v-icon>
          Load
        </v-btn>

        <v-dialog v-model="configDialog" width="600px">
          <template v-slot:activator="{ on, attrs }">
            <v-btn color="info" class="mt-5 ml-2" @click="configDialog = true" v-on="on" v-bind="attrs">
              <v-icon>mdi-cog</v-icon>
              Config
            </v-btn>
          </template>
          <v-card>
            <v-card-title>
              <h5>Feed Configuration</h5>
            </v-card-title>

            <v-card-text>
              <v-row>
                <v-textarea
                    v-model="postDescriptionDefault"
                    label="Post Description Default"
                    id="postDescriptionDefault"
                    outlined
                    rows="2"
                    :value="postDescriptionDefault"
                >
                </v-textarea>
              </v-row>
            </v-card-text>

            <v-card-actions>
              <v-btn color="success" @click="() => this.updateActiveItem(true)">
                <v-icon>mdi-checkbox-marked</v-icon>
                Exit
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>
      </v-row>

      <v-row v-if="this.subredditFeedItems.length > 0" no-gutter>
        <v-col cols="5" style="height: 500px; overflow-y: scroll;">
          <v-row v-for="item in this.subredditFeedItems" :key="item.id" @click="() => setActiveItem(item)">
            <v-col cols="4">
              <v-img :lazy-src="item.url" :src="item.url" contain max-height="150" max-width="150"></v-img>
            </v-col>
            <v-col cols="8" class="mt-2">
              <v-row>
                <h6 class="text-subtitle-1">{{ item.title }}</h6>
              </v-row>

              <v-row>
                <v-chip color="success" class="ma-2">
                  <v-icon size="12">mdi-arrow-up</v-icon>
                  {{ item.score }}
                </v-chip>
                <v-chip color="info" class="ma-2 pa-2">
                  <span class="text-grey-darken-1">{{ formatTime(item.created_utc) }}</span>
                </v-chip>
                <v-chip color="red" class="ma-2 pa-2" v-if="item.repost">
                  <span class="text-grey-darken-1">Scheduled</span>
                </v-chip>
              </v-row>
            </v-col>
          </v-row>
        </v-col>
        <v-col cols="7">
          <v-row>
            <v-col cols="10" offset="1" class="text-center">
              <h3 class="text-blue-lighten-1">{{ this.activeItem.title }}</h3>
            </v-col>
          </v-row>

          <v-row>
            <v-col cols="5" offset="1">
              <v-img :lazy-src="this.activeItem.url" :src="this.activeItem.url" contain max-height="500"
                     max-width="500"></v-img>
            </v-col>

            <v-col cols="6">
              <v-card elevation="2">
                <v-card-title class="mb-1">Repost Configuration</v-card-title>
                <v-card-text>
                  <v-row align="center" class="mt-1">
                    <v-textarea outlined name="post-description" v-model="postDescription"
                                :value="this.postDescription"
                                label="Post Description" required></v-textarea>
                  </v-row>

                  <v-row align="center" class="mt-1">
                    <v-text-field outlined name="post-when" v-model="postWhen" :value="this.postWhen"
                                  label="Post When" required></v-text-field>
                  </v-row>

                  <v-row align="center" class="mt-1">
                    <v-text-field outlined name="post-platforms" v-model="postPlatforms"
                                  :value="this.postPlatforms"
                                  label="Post Platforms" required></v-text-field>
                  </v-row>
                </v-card-text>

                <v-card-actions>
                  <v-btn color="success lighten-1" @click="() => schedulePost(this.activeItem)">
                    <v-icon>mdi-calendar-plus</v-icon>
                    Schedule Post
                  </v-btn>
                </v-card-actions>
              </v-card>
            </v-col>
          </v-row>
        </v-col>
      </v-row>

      <v-row
          v-else-if="this.loadAttempt === true && this.subredditFeedItems.length === 0">
        <v-col cols="12">
          <v-alert type="error" border="left" prominent>
            No feed items to load.
            <small>(Check console for errors)</small>
          </v-alert>
        </v-col>
      </v-row>

      <v-row v-else>
        <v-col cols="12">
          <v-alert type="info" border="left" prominent>
            Loading feed items.
          </v-alert>
        </v-col>
      </v-row>
    </v-form>
    <v-row>
      <v-snackbar v-model="snackbarToast" timeout="5000" :color="snackbarColor">
        <v-row>
          <v-col cols="8">
            <span class="text-subtitle-1">{{ snackbarMessage }}</span>

          </v-col>
          <v-col cols="4">
            <v-btn
                color="white"
                text
                v-bind="attrs"
                class="ml-2"
                @click="this.snackbarToast = false">
              Close
            </v-btn>

          </v-col>
        </v-row>

      </v-snackbar>
    </v-row>
  </v-container>

</template>

<script>
import {formatDistance} from "date-fns";
import $ from "jquery";

export default {
  name: "feed-importer",
  mounted() {
    console.log(`Initial subreddit load`);
    this.loadSubredditFeed();
  },
  data: () => ({
    feedSubreddit: "memes",
    feedSortType: "hot",
    sortTypes: ['hot', 'new', 'top', 'rising', 'controversial'],
    subredditFeedItems: [],
    activeItem: null,
    loadAttempt: false,
    configDialog: false,
    postWhen: "in 4 hours",
    postDescriptionDefault: "🎵 Stream Islati @ http://skreet.ca - PreSave \"Islati\" for October 30th Release 🎶",
    postDescription: "",
    postPlatforms: "facebook,twitter",
    snackbarToast: false, //whether or not the snackbar is showing.
    snackbarMessage: "", //the message to show in the snackbar.
    snackbarColor: "success"
  }),
  methods: {
    showSnackbar(message, color) {
      this.snackbarMessage = message;
      this.snackbarColor = color;
      this.snackbarToast = true;
    },
    schedulePost(item) {
      console.log(`Scheduling post ${item.id}`);
      let _post = null;
      for (let post of this.subredditFeedItems) {
        if (post.id !== item.id) {
          continue;
        }

        // this.snackbarMessage = `Post scheduled for reposting to ${this.postPlatforms} ${this.postWhen}`;
        // this.snackbarToast = true;
        _post = post;
        break;
      }

      if (_post === null) {
        console.error(`Unable to find post ${item.id} in subreddit feed items.`);
        return;
      }

      let self = this;
      this.showSnackbar(`Scheduling post for reposting to ${this.postPlatforms} ${this.postWhen}`, "info");
      $.ajax({
        url: "http://localhost:5000/feed-importer/schedule/",
        type: "POST",
        crossDomain: true,
        data: {
          postId: _post.id,
          postUrl: _post.url,
          body: self.postDescription,
          time: self.postWhen,
          platforms: self.postPlatforms,
          tags: [],
          subreddit: self.feedSubreddit,
          sortType: self.feedSortType
        },
        dataType: "json",
        success: function (data) {
          self.showSnackbar(data['message'], "success");
          _post.repost = true;
        },
        error: function (xhr, status) {
          console.log(`Error: ${status}`);
          console.log(xhr);
          console.log(status);
          self.showSnackbar(xhr['message'], "red");
        }
      });
    },
    setActiveItem(item) {
      console.log(`Setting active item: ${item.title}`);
      if (item === null || item === undefined) {
        this.activeItem = null;
        return;
      }
      this.activeItem = item;
      this.postDescription = `${item.title}\n${this.postDescriptionDefault}`;
    },
    updateActiveItem(closeDialog = false) {
      if (closeDialog === true) {
        this.configDialog = false;
      }
      this.postDescription = `${this.activeItem.title}\n${this.postDescriptionDefault}`;
    },
    loadSubredditFeed() {
      console.log("Loading feed for " + this.feedSubreddit + " sorted by " + this.feedSortType);

      // eslint-disable-next-line no-undef
      let self = this;
      $.ajax({
        url: "http://localhost:5000/feed-importer/load/",
        type: "POST",
        crossDomain: true,
        data: JSON.stringify({
          subreddit: this.feedSubreddit,
          sortType: this.feedSortType,
          limit: 100
        }),
        dataType: "json",
        success: function (data) {
          self.subredditFeedItems = data['posts'];
          console.log(`Loaded ${self.subredditFeedItems.length} items`);
          let firstItem = self.subredditFeedItems[0];
          if (firstItem === undefined || firstItem === null) {
            self.activeItem = null;
            console.log(`No items to load. Returned json from request:`);
            console.log(data);
            return;
          }
          self.setActiveItem(data['posts'][0]);
          console.log(`Active Item: ${self.activeItem}`);
        },
        error: function (xhr, status) {
          console.log(xhr);
          console.log(status);
        }
      }).always(function () {
        self.loadAttempt = true;
      });
    },
    formatTime(time) {
      const timeformat = formatDistance(new Date(time * 1000), new Date(), {addSuffix: true});
      return timeformat
    }
  }
}
</script>

<style scoped>

</style>