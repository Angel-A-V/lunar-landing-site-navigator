// Vite settings.
// The project lives on the Windows drive (/mnt/c) but Vite runs in WSL, and Windows does not
// tell WSL when a file changes. Polling makes Vite check the files itself instead.
export default {
  server: {
    watch: {
      usePolling: true,
    },
  },
};
