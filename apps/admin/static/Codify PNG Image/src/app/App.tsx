import trojanHorseImage from 'figma:asset/b6d249a4998553a07046b39ebec3be2a8a33e314.png';

export default function App() {
  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-gray-50 p-8">
      <div className="max-w-4xl w-full">
        <img 
          src={trojanHorseImage} 
          alt="Career Trojan - Network diagram showing career progression as a horse with interconnected nodes"
          className="w-full h-auto"
        />
      </div>
    </div>
  );
}
