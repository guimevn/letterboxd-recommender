// Em producao (Cloudflare Pages), aponta para a URL do backend no Render.
// Se o Render gerar uma URL diferente, basta atualizar a string abaixo.
window.API_BASE_URL =
  window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost'
    ? ''
    : 'https://letterboxd-recommender-api.onrender.com';
