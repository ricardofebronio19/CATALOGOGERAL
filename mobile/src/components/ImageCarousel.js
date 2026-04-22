import React, { useState, useRef } from 'react';
import { View, StyleSheet, FlatList, TouchableOpacity, Dimensions, Text } from 'react-native';
import { Image } from 'expo-image';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const IMG_HEIGHT = 260;

export default function ImageCarousel({ urls }) {
  const [activeIndex, setActiveIndex] = useState(0);
  const [fullscreen, setFullscreen] = useState(false);

  if (!urls || urls.length === 0) return null;

  const onScroll = (e) => {
    const idx = Math.round(e.nativeEvent.contentOffset.x / SCREEN_WIDTH);
    setActiveIndex(idx);
  };

  return (
    <View style={styles.container}>
      <FlatList
        data={urls}
        horizontal
        pagingEnabled
        showsHorizontalScrollIndicator={false}
        onScroll={onScroll}
        scrollEventThrottle={16}
        keyExtractor={(_, i) => String(i)}
        renderItem={({ item }) => (
          <TouchableOpacity onPress={() => setFullscreen(true)} activeOpacity={0.9}>
            <Image
              source={{ uri: item }}
              style={styles.image}
              contentFit="contain"
              transition={200}
              cachePolicy="memory-disk"
            />
          </TouchableOpacity>
        )}
      />

      {/* Dots */}
      {urls.length > 1 && (
        <View style={styles.dots}>
          {urls.map((_, i) => (
            <View
              key={i}
              style={[styles.dot, i === activeIndex && styles.dotActive]}
            />
          ))}
        </View>
      )}

      {/* Contador */}
      {urls.length > 1 && (
        <View style={styles.counter}>
          <Text style={styles.counterText}>{activeIndex + 1}/{urls.length}</Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#fff',
    borderRadius: 12,
    overflow: 'hidden',
    marginBottom: 12,
    elevation: 2,
  },
  image: {
    width: SCREEN_WIDTH - 24,
    height: IMG_HEIGHT,
    backgroundColor: '#F5F5F5',
  },
  dots: {
    flexDirection: 'row',
    justifyContent: 'center',
    paddingVertical: 8,
    gap: 6,
  },
  dot: {
    width: 7,
    height: 7,
    borderRadius: 4,
    backgroundColor: '#BDBDBD',
  },
  dotActive: { backgroundColor: '#1565C0', width: 18 },
  counter: {
    position: 'absolute',
    top: 10,
    right: 14,
    backgroundColor: 'rgba(0,0,0,0.45)',
    borderRadius: 10,
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  counterText: { color: '#fff', fontSize: 12 },
});
