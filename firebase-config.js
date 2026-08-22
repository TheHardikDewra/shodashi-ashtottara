/* ========================================
   Firebase configuration for cloud sync.

   These values are public identifiers, not secrets - data access
   is enforced by firestore.rules (a signed-in user can only touch
   documents under their own uid).

   All the sadhana apps share ONE Firebase project, so a single
   login works everywhere. `appId` below is the per-app namespace
   (the doc id under users/{uid}/apps/), and `fields` maps this
   app's localStorage keys onto how each one merges across devices.

   While apiKey/projectId are still REPLACE_ME, sync.js stays fully
   dormant and the app runs exactly as it did before, offline-first.
   ======================================== */

window.SADHANA_SYNC_CONFIG = {
  appId: 'shodashi-ashtottara',
  deviceKey: 'sh_device_id',
  fields: [
    { name: 'learned',  key: 'sh_learned',        merge: 'idset'     },
    { name: 'srs',      key: 'sh_srs',            merge: 'srs'       },
    { name: 'notes',    key: 'sh_notes',          merge: 'notes'     },
    { name: 'sadhana',  key: 'sh_sadhana',        merge: 'sadhana'   },
    { name: 'chantPos', key: 'sh_chant_pos',      merge: 'bookmark'  },
  ],
  firebase: {
    apiKey: 'REPLACE_ME',
    authDomain: 'REPLACE_ME.firebaseapp.com',
    projectId: 'REPLACE_ME',
    storageBucket: 'REPLACE_ME.firebasestorage.app',
    messagingSenderId: 'REPLACE_ME',
    appId: 'REPLACE_ME',
  },
};
