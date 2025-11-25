import path from 'path';
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, '.', '');
    return {
        base: './',
        server: {
            port: 3000,
            host: '0.0.0.0',
            allowedHosts: [
                'progress-strengthening-interface-desired.trycloudflare.com',
                'pansy-unsevere-lester.ngrok-free.dev',
                'seen-several-end-dts.trycloudflare.com',
                'bumpy-camels-feel.loca.lt', // allow localtunnel domain
                'localhost'
            ]
        },
        plugins: [react()],
        define: {
            'process.env.API_KEY': JSON.stringify(env.GEMINI_API_KEY || ''),
            'process.env.GEMINI_API_KEY': JSON.stringify(env.GEMINI_API_KEY || '')
        },
        resolve: {
            alias: {
                '@': path.resolve('.'),
            }
        }
    };
});
