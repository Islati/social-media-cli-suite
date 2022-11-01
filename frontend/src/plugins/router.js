import {createRouter, createWebHashHistory} from 'vue-router';
// import Homepage from "@/components/Homepage";
import FeedImporter from "@/components/RedditFeedImporter";
import ScheduledPosts from "@/components/ScheduledPosts";

const routes = [
    {path: '/', component: FeedImporter},
    {path: '/feed-importer', component: FeedImporter},
    {path: '/calendar', component: ScheduledPosts},
];

export default createRouter({
    history: createWebHashHistory(),
    routes: routes
})