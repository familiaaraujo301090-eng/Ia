import { app } from './app.js';
import { aiEnabled } from './ai.js';
import { startReminderLoop } from './extras.js';

const PORT = Number(process.env.PORT || 3000);
app.listen(PORT, () => {
  startReminderLoop();
  console.log(`Rumo rodando em http://localhost:${PORT}`);
  console.log(aiEnabled ? 'IA: Claude conectado.' : 'IA: modo demonstração (defina ANTHROPIC_API_KEY para ativar o Claude).');
});
