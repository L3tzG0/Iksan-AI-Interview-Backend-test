import path from 'path';
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, '.', '');
    return {
        // IMPORTANT for Netlify + React Router (BrowserRouter):
        // use an absolute base so assets resolve correctly on deep links like /teacher/home.
        base: '/',
        server: {
            port: 3000,
            host: '0.0.0.0',
            allowedHosts: [
                'antibodies-trainer-phillips-sullivan.trycloudflare.com',
                'pansy-unsevere-lester.ngrok-free.dev',
                'seen-several-end-dts.trycloudflare.com',
                'bumpy-camels-feel.loca.lt', // allow localtunnel domain
                'localhost'
            ]
        },
        plugins: [react()],
        define: {
            'process.env.API_KEY': JSON.stringify(geminiApiKey),
        },
        resolve: {
            alias: {
                '@': path.resolve('.'),
            }
        }
    };
});
