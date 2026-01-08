import type jsPDF from 'jspdf';

let cachedRegular: string | null = null;
let cachedBold: string | null = null;

const arrayBufferToBase64 = (buffer: ArrayBuffer) => {
  let binary = '';
  const bytes = new Uint8Array(buffer);
  const chunkSize = 0x8000;
  for (let i = 0; i < bytes.length; i += chunkSize) {
    binary += String.fromCharCode(...bytes.subarray(i, i + chunkSize));
  }
  return btoa(binary);
};

const loadFont = async (path: string) => {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`Failed to load font at ${path}`);
  }
  const buffer = await response.arrayBuffer();
  return arrayBufferToBase64(buffer);
};

export const ensurePdfFont = async (pdf: jsPDF) => {
  if (!cachedRegular) {
    cachedRegular = await loadFont('/fonts/NotoSansKR-Regular.ttf');
  }
  if (!cachedBold) {
    cachedBold = await loadFont('/fonts/NotoSansKR-Bold.ttf');
  }

  pdf.addFileToVFS('NotoSansKR-Regular.ttf', cachedRegular);
  pdf.addFont('NotoSansKR-Regular.ttf', 'NotoSansKR', 'normal');
  pdf.addFileToVFS('NotoSansKR-Bold.ttf', cachedBold);
  pdf.addFont('NotoSansKR-Bold.ttf', 'NotoSansKR', 'bold');
};
