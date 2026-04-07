#!/usr/bin/env node
/**
 * Auto Skill Finder - ClawHub 자동 스킬 검색 및 설치
 * 주인님의 요청을 분석하여 필요한 스킬을 자동으로 찾아서 설치합니다
 */

const SKILL_KEYWORDS = {
  'email': {
    keywords: ['email', 'gmail', 'outlook', 'mail', 'inbox', 'send mail', '이메일', '메일'],
    skills: ['gmail-skill', 'email-skill', 'outlook-skill', 'email-parser'],
    description: '이메일 읽기/쓰기/관리'
  },
  'calendar': {
    keywords: ['calendar', 'schedule', 'google calendar', 'outlook calendar', '일정', '캘린더'],
    skills: ['google-calendar', 'calendar-skill', 'schedule-assistant'],
    description: '캘린더 및 일정 관리'
  },
  'weather': {
    keywords: ['weather', 'forecast', '날씨', '예보', '기상'],
    skills: ['weather', 'advanced-weather', 'meteo-skill'],
    description: '날씨 정보 및 예보'
  },
  'news': {
    keywords: ['news', 'rss', 'headlines', '뉴스', 'rss'],
    skills: ['news-aggregator', 'rss-reader', 'news-skill'],
    description: '뉴스 및 RSS 피드'
  },
  'social': {
    keywords: ['twitter', 'tweet', 'mastodon', 'bluesky', 'social', 'post', '트윗', 'sns'],
    skills: ['twitter-skill', 'mastodon-skill', 'bluesky-skill', 'social-poster'],
    description: '소셜 미디어 포스팅'
  },
  'finance': {
    keywords: ['stock', 'crypto', 'bitcoin', 'trading', 'finance', '주식', '코인', '비트코인'],
    skills: ['stock-tracker', 'crypto-skill', 'finance-assistant'],
    description: '주식 및 암호화폐'
  },
  'pdf': {
    keywords: ['pdf', 'document', 'docx', 'word', 'excel', 'spreadsheet', '문서'],
    skills: ['pdf-skill', 'docx-skill', 'document-processor'],
    description: 'PDF 및 문서 처리'
  },
  'image': {
    keywords: ['image', 'photo', 'picture', 'ocr', 'vision', '사진', '이미지', 'ocr'],
    skills: ['image-processor', 'ocr-skill', 'vision-assistant'],
    description: '이미지 처리 및 OCR'
  },
  'audio': {
    keywords: ['audio', 'voice', 'tts', 'podcast', 'sound', '음성', '목소리', '팟캐스트'],
    skills: ['tts-skill', 'audio-processor', 'podcast-assistant'],
    description: '음성 및 오디오 처리'
  },
  'database': {
    keywords: ['database', 'db', 'sqlite', 'postgres', 'mysql', 'sql', '데이터베이스'],
    skills: ['database-skill', 'sql-assistant', 'sqlite-manager'],
    description: '데이터베이스 관리'
  },
  'git': {
    keywords: ['git', 'github', 'gitlab', 'commit', 'push', 'pull request', 'pr'],
    skills: ['github-skill', 'git-assistant', 'code-review'],
    description: 'Git 및 GitHub 관리'
  },
  'cloud': {
    keywords: ['aws', 'gcp', 'azure', 's3', 'ec2', 'cloud', 'server', '클우드', '서버'],
    skills: ['aws-skill', 'gcp-skill', 'cloud-manager'],
    description: '클우드 서비스 관리'
  },
  'home': {
    keywords: ['home assistant', 'smart home', 'iot', 'hue', 'homekit', 'smart', '홈'],
    skills: ['home-assistant', 'smart-home', 'iot-controller'],
    description: '스마트 홈 및 IoT'
  },
  'messaging': {
    keywords: ['slack', 'discord', 'telegram', 'whatsapp', 'signal', 'message', '메시지'],
    skills: ['slack-skill', 'discord-skill', 'messaging-assistant'],
    description: '메시징 플랫폼 연동'
  },
  'docker': {
    keywords: ['docker', 'container', 'kubernetes', 'k8s', 'terraform', '도커'],
    skills: ['docker-skill', 'kubernetes-skill', 'devops-assistant'],
    description: 'Docker 및 DevOps'
  },
  'browser': {
    keywords: ['browser', 'web', 'scraping', 'crawl', 'selenium', 'puppeteer', '웹', '크롤링'],
    skills: ['web-scraper', 'browser-automation', 'selenium-skill'],
    description: '웹 브라우저 자동화'
  },
  'video': {
    keywords: ['video', 'youtube', 'ffmpeg', 'movie', '동영상', '유튜브', '비디오'],
    skills: ['youtube-skill', 'video-processor', 'ffmpeg-skill'],
    description: '비디오 처리'
  }
};

// 요청에서 필요한 카테고리 감지
function detectCategories(request) {
  const lower = request.toLowerCase();
  const detected = [];
  
  for (const [category, data] of Object.entries(SKILL_KEYWORDS)) {
    if (data.keywords.some(k => lower.includes(k.toLowerCase()))) {
      detected.push({ category, ...data });
    }
  }
  
  return detected;
}

// 스킬 설치 명령 생성
function generateInstallCommands(skills) {
  return skills.map(skill => `openclaw skills install ${skill}`).join('\n');
}

// 메인 함수
function main() {
  const request = process.argv.slice(2).join(' ');
  
  if (!request) {
    console.log('🦞 Auto Skill Finder - ClawHub 스킬 자동 검색\n');
    console.log('사용법: node auto-skill-finder.js <"요청 내용">');
    console.log('예시: node auto-skill-finder.js "Gmail에서 이메일 읽어줘"');
    console.log('\n감지 가능한 카테고리:');
    Object.entries(SKILL_KEYWORDS).forEach(([cat, data]) => {
      console.log(`  • ${cat}: ${data.description}`);
    });
    process.exit(0);
  }
  
  console.log('🔍 주인님의 요청을 분석 중...\n');
  console.log(`   요청: "${request}"\n`);
  
  const detected = detectCategories(request);
  
  if (detected.length === 0) {
    console.log('❓ 특정 스킬 카테고리를 감지하지 못했습니다.');
    console.log('   ClawHub에서 직접 검색이 필요할 수 있습니다.');
    console.log('\n💡 다음과 같이 요청해 보세요:');
    console.log('   - "Gmail에서 이메일 읽어줘"');
    console.log('   - "Twitter에 포스팅해줘"');
    console.log('   - "내 캘린더 일정 알려줘"');
    process.exit(0);
  }
  
  console.log(`✅ ${detected.length}개 카테고리 감지됨:\n`);
  
  detected.forEach((item, index) => {
    console.log(`  ${index + 1}. ${item.category.toUpperCase()}`);
    console.log(`     설명: ${item.description}`);
    console.log(`     추천 스킬: ${item.skills.join(', ')}`);
    console.log();
  });
  
  // 검색 쿼리 생성
  console.log('🔎 ClawHub 검색 쿼리:');
  detected.forEach(item => {
    item.skills.forEach(skill => {
      console.log(`   - "${skill} skill site:clawhub.ai"`);
    });
  });
  
  console.log('\n💡 다음 단계:');
  console.log('   1. 위 검색어로 ClawHub에서 스킬 검색');
  console.log('   2. 적절한 스킬 선택');
  console.log('   3. 설치 명령 실행');
  console.log('\n📝 설치 명령 예시:');
  console.log(generateInstallCommands(detected[0].skills.slice(0, 2)));
}

// 모듈로도 사용 가능
module.exports = { detectCategories, SKILL_KEYWORDS, generateInstallCommands };

// CLI 실행
if (require.main === module) {
  main();
}
