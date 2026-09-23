import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { carregarEnv, lerConfig, validarTokenTelegram } from '/home/nmaldaner/projetos/openpcbotv3/dist/config/env.js';
const cfg=JSON.parse(readFileSync(process.env.EXPLICAVIDEOS_CONFIG || new URL('../examples/oswork.json',import.meta.url),'utf8'));
const root=cfg.output;
const receipt=`${root}/verification/telegram-final.json`;
if(existsSync(receipt)){console.log('Final delivery already sent');process.exit(0);}
const publication=JSON.parse(readFileSync(`${root}/verification/publication.json`,'utf8'));
carregarEnv();const config=lerConfig();if(!validarTokenTelegram(config.telegramToken).ok||!config.chatPermitido)throw new Error('Invalid bot v3 configuration');
const base=`https://api.telegram.org/bot${config.telegramToken}/`;
const me=await(await fetch(base+'getMe')).json();if(!me.ok||me.result.username!=='inemav3bot')throw new Error('Unexpected bot identity');
const titles={pt:'Português',es:'Español',en:'English'};
const lines=Object.entries(publication.videos).map(([lang,v])=>`${titles[lang]} (${Math.floor(v.duration/60)}min${String(Math.floor(v.duration%60)).padStart(2,'0')}s):\n${v.url}`);
const text='Explicavideos e OSWork completo publicados.\n\nAvatar e voz do Nei, Oito módulos, 48 tópicos e 122 cenas ilustradas e legendas.\n\n'+lines.join('\n\n')+'\n\nVídeos e acesso ao curso:\nhttps://inematds.github.io/oswork/videos/\n\nProjeto e guia:\nhttps://inematds.github.io/explicavideos/guia/\n\nPortal:\nhttps://inema.club\n\nLegendas SRT e downloads:\n'+publication.release;
const response=await(await fetch(base+'sendMessage',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({chat_id:config.chatPermitido,text,link_preview_options:{is_disabled:true}})})).json();
if(!response.ok)throw new Error('Telegram delivery HTTP '+response.error_code);
writeFileSync(receipt,JSON.stringify({bot:me.result.username,message_id:response.result.message_id,date:response.result.date},null,2));console.log('Final links delivered to bot v3');
