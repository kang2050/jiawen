// Design: Tech-Warmth Futurism - 真实 Three.js 3D 查看器
// 使用 @react-three/fiber + @react-three/drei 加载真实 GLB 模型
import { Suspense, useRef } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, useGLTF, Center, Environment, Grid, Html } from "@react-three/drei";
import { RotateCcw, Download, Loader2 } from "lucide-react";

// ─── 真实 GLB 模型加载 ───────────────────────────────────────────────

function PetModel({ url }: { url: string }) {
  const { scene } = useGLTF(url);
  return (
    <Center>
      <primitive object={scene} />
    </Center>
  );
}

// ─── 占位模型（等待 GLB 时显示）────────────────────────────────────

function PlaceholderDog() {
  return (
    <group>
      {/* 躯干 */}
      <mesh position={[0, 0.3, 0]} castShadow>
        <boxGeometry args={[0.9, 0.45, 0.55]} />
        <meshStandardMaterial color="#d4a843" roughness={0.6} />
      </mesh>
      {/* 头部 */}
      <mesh position={[0.55, 0.62, 0]} castShadow>
        <boxGeometry args={[0.38, 0.38, 0.38]} />
        <meshStandardMaterial color="#d4a843" roughness={0.6} />
      </mesh>
      {/* 口鼻 */}
      <mesh position={[0.76, 0.55, 0]} castShadow>
        <boxGeometry args={[0.18, 0.2, 0.28]} />
        <meshStandardMaterial color="#c49433" roughness={0.7} />
      </mesh>
      {/* 耳朵 */}
      <mesh position={[0.52, 0.85, 0.14]} castShadow>
        <boxGeometry args={[0.12, 0.22, 0.08]} />
        <meshStandardMaterial color="#b8891e" roughness={0.8} />
      </mesh>
      <mesh position={[0.52, 0.85, -0.14]} castShadow>
        <boxGeometry args={[0.12, 0.22, 0.08]} />
        <meshStandardMaterial color="#b8891e" roughness={0.8} />
      </mesh>
      {/* 四腿 */}
      {(
        [
          [0.3, 0.04, 0.18],
          [-0.3, 0.04, 0.18],
          [0.3, 0.04, -0.18],
          [-0.3, 0.04, -0.18],
        ] as [number, number, number][]
      ).map((pos, i) => (
        <mesh key={i} position={pos} castShadow>
          <boxGeometry args={[0.12, 0.45, 0.12]} />
          <meshStandardMaterial color="#c49433" roughness={0.7} />
        </mesh>
      ))}
      {/* 尾巴 */}
      <mesh position={[-0.58, 0.52, 0]} rotation={[0, 0, 0.6]} castShadow>
        <cylinderGeometry args={[0.04, 0.03, 0.35, 8]} />
        <meshStandardMaterial color="#d4a843" roughness={0.6} />
      </mesh>
      {/* 地面阴影接收 */}
      <mesh position={[0, -0.23, 0]} receiveShadow rotation={[-Math.PI / 2, 0, 0]}>
        <planeGeometry args={[3, 3]} />
        <shadowMaterial opacity={0.15} />
      </mesh>
    </group>
  );
}

// ─── 加载中提示 ──────────────────────────────────────────────────────

function LoadingHint() {
  return (
    <Html center>
      <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-black/60 backdrop-blur-sm text-teal text-sm whitespace-nowrap">
        <Loader2 className="animate-spin" size={14} />
        <span>加载 3D 模型中...</span>
      </div>
    </Html>
  );
}

// ─── 主组件 ──────────────────────────────────────────────────────────

interface Props {
  glbUrl?: string | null;
  onDownload?: () => void;
}

export default function Model3DViewer({ glbUrl, onDownload }: Props) {
  const controlsRef = useRef<any>(null);

  return (
    <div className="relative w-full rounded-2xl overflow-hidden bg-[oklch(0.04_0.01_250)] border border-border/30">
      <div className="w-full aspect-[16/10] lg:aspect-[16/9]">
        <Canvas
          camera={{ position: [0, 1.2, 3.5], fov: 45 }}
          shadows
          gl={{ antialias: true, alpha: true }}
        >
          {/* 光照 */}
          <ambientLight intensity={0.5} />
          <directionalLight position={[5, 8, 5]} intensity={1.2} castShadow shadow-mapSize={[2048, 2048]} />
          <directionalLight position={[-4, 3, -4]} intensity={0.3} />
          <pointLight position={[0, 3, 0]} intensity={0.4} color="#00e5cc" />

          {/* 模型 */}
          <Suspense fallback={<LoadingHint />}>
            {glbUrl ? <PetModel url={glbUrl} /> : <PlaceholderDog />}
            <Environment preset="city" />
          </Suspense>

          {/* 地板网格 */}
          <Grid
            position={[0, -0.23, 0]}
            args={[10, 10]}
            cellColor="oklch(0.75 0.15 180 / 0.25)"
            sectionColor="oklch(0.75 0.15 180 / 0.5)"
            cellThickness={0.5}
            sectionThickness={1}
            fadeDistance={7}
            infiniteGrid
          />

          {/* 控制器：拖动旋转，滚轮缩放 */}
          <OrbitControls
            ref={controlsRef}
            autoRotate
            autoRotateSpeed={1.5}
            enablePan={false}
            minDistance={1.5}
            maxDistance={8}
            maxPolarAngle={Math.PI / 2.1}
            target={[0, 0.3, 0]}
          />
        </Canvas>
      </div>

      {/* 状态角标 */}
      <div className="absolute top-4 left-4 glass-card rounded-lg px-3 py-2 z-10 pointer-events-none">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-teal animate-pulse" />
          <span className="text-xs text-teal font-medium">
            {glbUrl ? "Three.js · 真实 GLB 模型" : "Three.js · 示例模型"}
          </span>
        </div>
      </div>

      {/* 操作按钮 */}
      <div className="absolute top-4 right-4 flex flex-col gap-2 z-10">
        <button
          onClick={() => controlsRef.current?.reset()}
          className="w-9 h-9 glass-card rounded-lg flex items-center justify-center text-muted-foreground hover:text-teal transition-colors"
          title="重置视角"
        >
          <RotateCcw size={16} />
        </button>
        {onDownload && glbUrl && (
          <button
            onClick={onDownload}
            className="w-9 h-9 glass-card rounded-lg flex items-center justify-center text-muted-foreground hover:text-teal transition-colors"
            title="下载 GLB"
          >
            <Download size={16} />
          </button>
        )}
      </div>

      {/* 底部提示 */}
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2 glass-card rounded-lg px-4 py-2 z-10 pointer-events-none">
        <span className="text-xs text-muted-foreground">拖动旋转 · 滚轮缩放 · 右键平移</span>
      </div>

      {/* 规格标签（无真实 GLB 时隐藏 "8K" 等假数据） */}
      {glbUrl && (
        <div className="absolute top-4 right-16 glass-card rounded-lg px-3 py-1.5 z-10 hidden sm:block pointer-events-none">
          <span className="text-[10px] font-medium text-teal tracking-wider uppercase">
            GLB · Three.js 渲染
          </span>
        </div>
      )}
    </div>
  );
}
