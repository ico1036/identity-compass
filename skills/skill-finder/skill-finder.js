#!/usr/bin/env node
/**
 * ClawHub 스킬 자동 검색 및 설치 스크립트
 * 주인님을 위해 필요한 스킬을 찾아서 설치합니다
 */

const { execSync } = require('child_process');

// 스킬 카테고리 매핑
const SKILL_CATEGORIES = {
  'email': ['email', 'gmail', 'outlook', 'mail'],
  'calendar': ['calendar', 'schedule', 'google-calendar', 'outlook-calendar'],
  'weather': ['weather', 'forecast', 'meteo'],
  'coding': ['coding', 'codex', 'claude-code', 'programming', 'github'],
  'news': ['news', 'rss', 'headlines'],
  'finance': ['finance', 'stock', 'crypto', 'trading'],
  'social': ['twitter', 'mastodon', 'bluesky', 'social'],
  'search': ['search', 'web-search', 'brave', 'google'],
  'image': ['image', 'vision', 'ocr', 'photo'],
  'audio': ['audio', 'tts', 'stt', 'voice', 'podcast'],
  'video': ['video', 'youtube'],
  'database': ['database', 'db', 'sqlite', 'postgres'],
  'automation': ['automation', 'workflow', 'ifttt', 'zapier'],
  'health': ['health', 'fitness', 'workout'],
  'home': ['home', 'smart-home', 'iot', 'home-assistant'],
  'security': ['security', 'audit', 'scan'],
  'messaging': ['message', 'notification', 'alert'],
  'file': ['file', 'pdf', 'document', 'spreadsheet'],
  'git': ['git', 'github', 'gitlab', 'version-control'],
  'docker': ['docker', 'container', 'kubernetes'],
  'cloud': ['aws', 'gcp', 'azure', 'cloud'],
};

// 입력받은 작업에 따라 필요한 스킬 카테고리 결정
function detectSkillCategory(input) {
  const lower = input.toLowerCase();
  const matched = [];
  
  for (const [category, keywords] of Object.entries(SKILL_CATEGORIES)) {
    if (keywords.some(k => lower.includes(k))) {
      matched.push(category);
    }
  }
  
  return matched;
}

// ClawHub에서 스킬 검색
async function searchClawHub(keyword) {
  console.log(`🔍 ClawHub에서 "${keyword}" 관련 스킬 검색 중...`);
  
  try {
    // 실제로는 web_search 도구를 통해 검색
    // 여기서는 검색어 생성만
    const searchQueries = [
      `${keyword} skill site:clawhub.ai`,
      `${keyword} openclaw skill`,
      `clawhub ${keyword}`
    ];
    
    return searchQueries;
  } catch (error) {
    console.error('검색 중 오류:', error);
    return [];
  }
}

// 메인 함수
async function main() {
  const userInput = process.argv.slice(2).join(' ');
  
  if (!userInput) {
    console.log('사용법: node skill-finder.js <"필요한 작업 설명">');
    console.log('예시: node skill-finder.js "이메일 본문 요약"');
    process.exit(1);
  }
  
  console.log('🎯 주인님의 요청 분석 중...');
  console.log(`   요청: "${userInput}"`);
  
  const categories = detectSkillCategory(userInput);
  
  if (categories.length === 0) {
    console.log('❓ 특정 카테고리를 감지하지 못했습니다.');
    console.log('   ClawHub에서 직접 검색을 시도합니다...');
    categories.push('general');
  } else {
    console.log(`✅ 감지된 카테고리: ${categories.join(', ')}`);
  }
  
  // 각 카테고리별로 검색
  for (const category of categories) {
    console.log(`\n📦 "${category}" 관련 스킬 검색 중...`);
    const queries = await searchClawHub(category);
    console.log('   검색어:', queries);
  }
  
  console.log('\n💡 이 스크립트는 실제 스킬 검색을 위해 web_search 도구를 사용해야 합니다.');
  console.log('   OpenClaw 세션에서 실행하세요.');
}

if (require.main === module) {
  main();
}

module.exports = { detectSkillCategory, searchClawHub };
